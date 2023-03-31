from app import app
from waitress import serve

if __name__ == '__main__':
    app.run(debug=False)
