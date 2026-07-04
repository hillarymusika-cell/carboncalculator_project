from flask import render_template ,Flask,request
app = Flask(__name__)
@app.route('/login',methods=['GET','POST'])
def login():
    email=request.form.get("email")
    password=request.form.get("password")
    print(f"Email:{email} password: {password}")
    return render_template('login.html')
if __name__ =='__main__':   
    app.run(debug="True")