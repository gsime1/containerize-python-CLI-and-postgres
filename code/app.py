import argparse
import psycopg2


parser = argparse.ArgumentParser(prog='app.py')
parser.add_argument('file', help='path to csv file containing the url ids to be queried.')
parser.add_argument('--add', help='use --add flag to add file content to table.', action="store_true")
parser.add_argument('--dump', help='use --dump flag to dump data from table to new file.', action="store_true")

ARGS = parser.parse_args()
PATH = ARGS.file
ADD = ARGS.add
DUMP = ARGS.dump

if __name__ == "__main__":
    
    conn = psycopg2.connect(dbname="ch_db", 
                            user="ch_user", 
                            password="ch_pass", 
                            host="ch_pg", 
                            port="5432")
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS test_app (
                                              id serial PRIMARY KEY,
                                              alpha_ls varchar, 
                                              data varchar);""")

    conn.commit()
    if ADD:

        print("The --add flag was passed, reading and inserting these lines in the db:\n")
        
        with open(PATH, "r") as f:
        
            for line in f:
            
                print(line) 

                words_ls = line.split()
                
                cur.execute("""INSERT INTO test_app (alpha_ls, data) 
                                             VALUES (%s, %s);""",
                                                    (words_ls[0], words_ls[1]))
                conn.commit()
    if DUMP:

        print("The --dump flag was passed.\n")
        
        cur.execute("SELECT * FROM test_app;")
        
        data = cur.fetchall()

        with open("./dump.txt", "w") as f:  # w creates file if doesn't exist.
            
            f.writelines(f"{record}\n" for record in data)
            
        print("the following lines were written to file\n")

        with open("./dump.txt", "r") as f:
            for line in f:
                print(line)
