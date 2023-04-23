import pymysql
from app import app
from db_config import mysql
from flask import jsonify
from flask import flash, request

# Get number of cars in the table
@app.route('/cars/count')
def carsCount():
    try:
        # MySQL connection
        conn = mysql.connect()
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM cars")
        total_cars = cur.fetchone()[0]

        resp = jsonify({'total': total_cars})
        resp.status_code = 200

        cur.close()
        conn.close()

        return resp

    except Exception as e:
        resp = jsonify({'error': str(e)})
        resp.status_code = 500
        return resp

@app.route('/cars', methods=['GET'])
def cars():
    try:
        args = request.args
        model = args.get('model')
        year = args.get('year')
        # Use 'id' as default orderBy value
        orderBy = args.get('orderBy', 'id')
        # Use 'ASC' as default orderAscDesc value
        orderAscDesc = args.get('orderAscDesc', 'ASC')
        limit = int(args.get('limit', 10))  # Use 10 as default limit value
        pageNo = int(args.get('pageNo', 1))  # Use 1 as default pageNo value

        whereClauses = []
        if model is not None:
            whereClauses.append(f"model = '{model}'")
        if year is not None:
            whereClauses.append(f"year = '{year}'")

        with mysql.connect() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cur:
                whereString = "WHERE " + \
                    " AND ".join(whereClauses) if whereClauses else ""
                query = f"SELECT * FROM cars {whereString} ORDER BY {orderBy} {orderAscDesc} LIMIT {limit} OFFSET {(pageNo - 1) * limit}"
                cur.execute(query)
                rows = cur.fetchall()
                print("Records returned:", len(rows))

        if len(rows) > 0:
            return jsonify(rows), 200
        else:
            message = {
                'status': 404,
                'message': 'The table is empty'
            }
            return jsonify(message), 404

    except Exception as e:  # return errors in a JSON format
        message = {
            'status': 500,
            'message': 'Error: ' + str(e)
        }
        return jsonify(message), 500

@app.route('/cars/<int:id>')
def view_cars(id):
    try:
        # MySQL connection
        conn = mysql.connect()
        cur = conn.cursor(pymysql.cursors.DictCursor)

        cur.execute("SELECT * FROM cars WHERE id = %s;", id)
        rows = cur.fetchall()

        if len(rows) > 0:
            return jsonify(rows[0]), 200
        else:
            message = {'status': 404,
                       'message': 'The car with the specified ID does not exist'}
            return jsonify(message), 404

    except Exception as e:
        message = {'status': 500, 'message': 'Error: ' + str(e)}
        return jsonify(message), 500

    finally:
        cur.close()
        conn.close()

@app.route('/cars/create', methods=['POST'])
def add_cars():
    try:
        model, year, price = request.form.get(
            'model'), request.form.get('year'), request.form.get('price')
        conn, cur = mysql.connect(), conn.cursor(pymysql.cursors.DictCursor)
        if model and year and price:
            cur.execute(
                "INSERT INTO cars(model, year, price) VALUES(%s, %s, %s)", (model, year, price))
            conn.commit()
            message = {'status': 200,
                       'message': 'The car was created successfully'}
            resp = jsonify(message)
            resp.status_code = 200
        else:
            message = {'status': 510,
                       'message': 'Some of the fields are empty'}
            resp = jsonify(message)
            resp.status_code = 510
        cur.close()
        conn.close()
        return resp
    except Exception as e:
        message = {'status': 500, 'message': 'Error: '+str(e)}
        resp = jsonify(message)
        resp.status_code = 500
        return resp

@app.route('/cars/delete/<int:id>')
def delete_cars(id):
    try:
        # MySQL connection
        conn = mysql.connect()
        cur = conn.cursor(pymysql.cursors.DictCursor)

        cur.execute("DELETE FROM cars WHERE id = %s;", id)
        if cur.rowcount > 0:
            conn.commit()
            message = {
                'status': 200,
                'message': 'The cars with ID '+str(id)+' was deleted successfully'
            }
            resp = jsonify(message)
            resp.status_code = 200
        else:
            message = {
                'status': 414,
                'message': 'The car with the ID specified does NOT exist'
            }
            resp = jsonify(message)
            resp.status_code = 414

        cur.close()
        conn.close()

        return resp

    except Exception as e:
        message = {
            'status': 500,
            'message': 'Error: '+str(e)
        }
        resp = jsonify(message)
        resp.status_code = 500
        return resp

@app.route('/cars/edit', methods=['POST'])
def edit_cars():
    try:
        id, model, year, price = request.form.get('carsId'), request.form.get(
            'model'), request.form.get('year'), request.form.get('price')

        conn, cur = mysql.connect(), conn.cursor(pymysql.cursors.DictCursor)

        if all([model, year, price]):
            sql = "UPDATE cars SET model=%s,year=%s,price=%s WHERE id=%s;"
            cur.execute(sql, (model, year, price, id))
            conn.commit()

            resp = jsonify(
                {'status': 200, 'message': 'The car was modified successfully'})
            resp.status_code = 200

        else:
            resp = jsonify(
                {'status': 510, 'message': 'Some of the fields are empty'})
            resp.status_code = 510

        cur.close()
        conn.close()

        return resp

    except Exception as e:
        return jsonify({'status': 500, 'message': f'Error: {str(e)}'}), 500

@app.route('/cars/login', methods=['POST'])
def login():
    try:
        model = request.form['model']
        password = request.form['password']
        conn = mysql.connect()
        cur = conn.cursor(pymysql.cursors.DictCursor)
        cur.execute(
            f"SELECT * FROM cars WHERE model='{model}' AND year='{password}'")
        rows = cur.fetchall()
        cur.close()
        conn.close()

        message = {'status': 200, 'message': 'OK'} if len(
            rows) > 0 else {'status': 404, 'message': 'model not found, please try again'}
        resp = jsonify(message)
        resp.status_code = message['status']
        return resp

    except Exception as e:
        resp = jsonify({'status': 500, 'message': f'Error: {e}'})
        resp.status_code = 500
        return resp

@app.errorhandler(404)
def not_found(error=None):
    return jsonify({'status': 404, 'message': 'Not found: '+request.url}), 404

if __name__ == "__main__":
    app.run()