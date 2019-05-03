from flask import Flask, render_template
from settings import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from extensions import bootstrap, db, login_manager, csrf
import os

app = Flask(__name__)
app.config.from_object(Config)
migrate = Migrate(app, db)
bootstrap.init_app(app)
db.init_app(app)
login_manager.init_app(app)
csrf.init_app(app)

import routes, models


if __name__ == '__main__':
    app.run()
