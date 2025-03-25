import sqlite3

# Connect to your database
con = sqlite3.connect('db.sqlite3')
cursor = con.cursor()

# Check if the column already exists
cursor.execute("PRAGMA table_info(core_projectfile)")
columns = cursor.fetchall()
column_names = [column[1] for column in columns]

if 'milestone_id' not in column_names:
    print("Adding milestone_id column to core_projectfile table...")
    cursor.execute("ALTER TABLE core_projectfile ADD COLUMN milestone_id integer REFERENCES core_projectmilestone(id) ON DELETE SET NULL")
    print("Column added successfully!")
else:
    print("milestone_id column already exists in core_projectfile table.")

# Check if the completion_notes column exists in core_projectmilestone
cursor.execute("PRAGMA table_info(core_projectmilestone)")
columns = cursor.fetchall()
column_names = [column[1] for column in columns]

if 'completion_notes' not in column_names:
    print("Adding completion_notes column to core_projectmilestone table...")
    cursor.execute("ALTER TABLE core_projectmilestone ADD COLUMN completion_notes text NULL")
    print("Column added successfully!")
else:
    print("completion_notes column already exists in core_projectmilestone table.")

if 'completed_at' not in column_names:
    print("Adding completed_at column to core_projectmilestone table...")
    cursor.execute("ALTER TABLE core_projectmilestone ADD COLUMN completed_at datetime NULL")
    print("Column added successfully!")
else:
    print("completed_at column already exists in core_projectmilestone table.")

if 'feedback' not in column_names:
    print("Adding feedback column to core_projectmilestone table...")
    cursor.execute("ALTER TABLE core_projectmilestone ADD COLUMN feedback text NULL")
    print("Column added successfully!")
else:
    print("feedback column already exists in core_projectmilestone table.")

# Commit the changes and close the connection
con.commit()
con.close()

print("Database update completed!") 