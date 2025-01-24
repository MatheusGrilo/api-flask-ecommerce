#
README.md

## How to test

1. Install Python 3.13.

2. Install required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Set up the database:

   ```bash
   flask shell
   db.drop_all()
   db.create_all()
   db.session.commit()
   exit()
   ```

4. Start the project:

   ```bash
   python app.py
   ```

