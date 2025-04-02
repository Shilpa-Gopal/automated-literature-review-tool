from flask import Flask

app = Flask(__name__)

@app.route('/api', methods=['GET'])
def home():
    return {"message": "API is working"}

@app.route('/api/test', methods=['GET'])
def test():
    return {"message": "Test endpoint is working"}

# Must have this for Vercel serverless functions
if __name__ == '__main__':
    app.run()
