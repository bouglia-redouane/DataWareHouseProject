import psycopg
class PostgreSQLConnection:
    def __init__(self, dbname, user, password, host='localhost', port=5432):
        self.dbname = dbname
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.conn = None
        self.connect()

    def connect(self):
        try:
            self.conn = psycopg.connect(
                dbname=self.dbname,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port
            )
            print("Connected to PostgreSQL database!")
        except psycopg.Error as e:
            print("Error: Unable to connect to the PostgreSQL database.")
            print(e)

    def setup(self, setup_file):
        try:
            with open(setup_file, 'r') as file:
                sql_queries = file.read()
            queries = sql_queries.split(';')
            cursor = self.conn.cursor()
            for query in queries:
                if query.strip():
                    cursor.execute(query)
                    self.conn.commit()
            cursor.close()
            print("SQL file executed successfully!")

        except psycopg.Error as e:
            print("Error: Unable to connect to the PostgreSQL database or execute SQL file.")
            print(e)

    def insert_course_into_table(self, course_item):
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO Course (id, title, url, description, img_url, rating, num_reviews, duration, price, level, course_type, sub_categorie_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                course_item['id'],
                course_item['title'],
                course_item['url'],
                course_item['desc'],
                course_item['img_url'],
                course_item['rating'],
                course_item['num_reviews'],
                course_item['duration'],
                course_item['price'],
                course_item['level'],
                course_item['type'],
                course_item['sub_categorie_id']
            ))
            self.conn.commit()

            print("Course inserted successfully!")

            cursor.close()

        except psycopg.Error as e:
            print("Error: Unable to connect to the PostgreSQL database or execute query.")
            print(e)


pg_conn = PostgreSQLConnection(dbname='big_format_db', user='redouane', password='redouane')
pg_conn.setup("/media/redouane/Data/Data Warehouse/project/DataWareHouse/scraping/files/db_setup.txt")
course_item = {
        'id': 'course_001',
        'title': 'Introduction to Python',
        'url': 'https://www.example.com/courses/python',
        'desc': 'This course provides an introduction to the Python programming language.',
        'img_url': 'https://www.example.com/images/python.jpg',
        'rating': '4.5',
        'num_reviews': '100',
        'duration': '6 weeks',
        'price': '99.99',
        'level': 'Beginner',
        'type': 'Online',
        'sub_categorie_id': 'sub_category_001'
    }
    # Insert course into Course table
pg_conn.insert_course_into_table(course_item)
