from operator import itemgetter
from re import match

from flask import Flask, render_template, request, redirect

import database

app = Flask(__name__)


connection = database.connect()
database.create_tables(connection)



def validation_enter(login, password):
    connection = database.connect()
    database_answer = database.get_user_by_login(connection, login)
    if database_answer:
        if database_answer[0][2] != password:
            return False, 'Неверный пароль'
    else:
        return False, 'Нет такого логина'
    return True, ''



def validation_reg(login, password, password_check):
    connection = database.connect()

    if len(database.get_user_by_login(connection, login)) > 0:
        return False, 'Пользователь с таким ником уже существует'
    if password_check != password:
        return False, 'Пароли не совпадают'
    if len(password) < 8:
        return False, 'Ненадежный пароль'
    if not match(r'[a-zA-Z0-9]', login):
        return False, 'Логин должен состоять только из английских букв и цифр'
    return True, ''



@app.route('/')
def main_page():
    return redirect('/enter')



@app.route('/enter', methods=['GET', 'POST'])
def enter():
    if request.method == 'POST':
        login = request.form.get('login')
        password = request.form.get('password')
        is_valid, error_text = validation_enter(login, password)
        if is_valid:
            res = redirect('/test')
            res.set_cookie('test_login', login)
            return res
        else:
            return render_template('enter.html', error=(True, error_text),
                                   reg_link='/reg')

    if not request.cookies.get('test_login'):
        return render_template('enter.html', error=(False, ''),
                               reg_link='/reg')
    else:
        return redirect('/test')



@app.route('/reg', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        login = request.form.get('login')
        password = request.form.get('password')
        password_check = request.form.get('password_check')
        print('DATA: ', login, password, password_check)
        is_valid, error_text = validation_reg(login, password, password_check)
        if is_valid:
            connection = database.connect()
            database.add_user(connection, login, password)
            return redirect('/enter')
        else:
            return render_template('reg.html', error=(True, error_text))
    return render_template('reg.html', error=(False, ''))



@app.route('/test', methods=['GET', 'POST'])
def test():
    login = request.cookies.get('test_login')
    connection = database.connect()

    if not login:
        return redirect('/enter')
    if request.method == 'POST':
        if 'exit' in request.form:
            res = redirect('/enter')
            res.set_cookie('test_login', '', max_age=0)
            return res
        else:
            points = 0
            answers = []

            questions = database.get_all_questions(connection)
            for question in questions:
                id, correct_answer = str(question[0]), str(question[6])
                answer = request.form.get(id)
                answers.append(answer)
                if answer == correct_answer:
                    points += 1

            database.add_result(connection, login, ' '.join(answers), points)
            return redirect('/results')
    else:
        test = database.get_all_questions(connection)
        return render_template('test.html', login=login, test=test)



@app.route('/results', methods=['GET', 'POST'])
def result():
    login = request.cookies.get('test_login')
    if not login:
        return redirect('/enter')
    connection = database.connect()
    results = database.get_all_results(connection)
    results = [elem[1:] for elem in results]
    heading = ['Логин', 'Ответы', 'Баллы']
    #
    return render_template('results.html', heading=heading,
                           results=reversed(sorted(results, key=itemgetter(2, 0, 1))))


if __name__ == '__main__':
    app.debug = True
    app.run()
