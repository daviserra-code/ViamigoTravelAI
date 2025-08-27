from flask_app import app, create_tables
import routes  # noqa: F401

if __name__ == "__main__":
    # Create tables after all imports are complete
    create_tables()
    app.run(host="0.0.0.0", port=5000, debug=True)