import re

from db import get_connection, add_player, create_semester, create_session, create_round, record_match, get_pid_from_name

def split_to_sessions(semester_data):
    result = []
    current = []

    for item in semester_data:
        if item == ".":
            result.append(current)
            current = []
        else:
            current.append(item)

    result.append(current)

    result.append(result[0])
    
    result.pop(0)
    return result

def clean_to_sessions(sessions_data):
    sessions_data_copy = sessions_data.copy()
    sessions = []

    for k, i in enumerate(sessions_data):
        if i == ".":

            for j in range(k + 1, k + 999):
                try:
                    if sessions_data[j] == ".":
                        f = j - k
                        break
                except:
                    f = j - k
                    break

            sessions.append(sessions_data_copy[:f])

            for i in range(0, f):
                sessions_data_copy.pop(0)
                
    for session in sessions:
        session.pop(0)


    sessions.append(sessions_data[0])
    return sessions



with open("DB/raw_data.txt", "r") as file:
    raw_data = file.read()    
    
# Matches date format: DD.MM.YYYY
date_pattern = re.compile(r"^\d{2}\.\d{2}\.\d{4}$")

# Step 1: Split into main blocks by hash lines
main_blocks = [
    section.strip("\n").splitlines()
    for section in re.split(r"(?m)^#+.*$", raw_data)
    if section.strip()
]

# Step 2: Split each block into sub-lists at '.'
dot_parsed_data = []
for block in main_blocks:
    sub_lists = []
    current_sub = []
    for line in block:
        if line.strip() == ".":
            sub_lists.append(current_sub)
            current_sub = []
        else:
            current_sub.append(line)
    if current_sub:
        sub_lists.append(current_sub)
    dot_parsed_data.append(sub_lists)

# Step 3: Split by empty lines AND isolate dates into separate lists
final_parsed_data = []

for block in dot_parsed_data:
    block_groups = []
    for sub_list in block:
        groups = []
        current_group = []

        for line in sub_list:
            clean_line = line.strip()

            if not clean_line:  # Empty line separator
                if current_group:
                    groups.append(current_group)
                    current_group = []
            elif date_pattern.match(clean_line):  # Date isolated to its own list
                if current_group:
                    groups.append(current_group)
                    current_group = []
                groups.append([clean_line])
            else:
                current_group.append(clean_line)

        if current_group:
            groups.append(current_group)

        block_groups.append(groups)

    final_parsed_data.append(block_groups)
    
semesters_list = []
sessions_list = []
matches_list = []
players_set = set()

sem_format = r"^\d{4}\.\d{4}\.\d+$"
ses_format = r"^\d{2}\.\d{2}\.\d+$"

for sem in final_parsed_data:
    for session in sem:
        for round_ in session:
            
            #Per Semester Logic
            if re.match(sem_format, round_[0]):
                #print(f"Semester: {round_[0]}")
                pass
                
            #Per Session Logic
            elif re.match(ses_format, round_[0]):
                #print(f"Session: {round_[0]}")
                pass
                
            #Per Round Logic
            else:
                #print(f"Round: {round_}")
                
                for match in round_:
                    ls = match.split(",")
                    
                    def format_name(name):
                        name = name.lower()
                        name = name.title()
                        return name.strip()
                    
                    first_name1 = format_name(ls[0])                                              
                    last_name1 = format_name(ls[1])
                    p_name1 = (first_name1, last_name1)
                    
                    first_name2 = format_name(ls[2])
                    last_name2 = format_name(ls[3])
                    p_name2 = (first_name2, last_name2)
                    
                    players_set.add(p_name1)
                    players_set.add(p_name2)
                    
                    if ls[4]:
                        #player 1 won
                        matches_list.append((p_name1, p_name2, 1))
                    else:
                        #player 2 won
                        matches_list.append((p_name1, p_name2, 0))
                                
conn = get_connection()
                             
for player in list(players_set):
    add_player(conn, player[0], player[1])
    
for sem in final_parsed_data:
    for session in sem:
        for round_ in session:
            
            #Per Semester Logic
            if re.match(sem_format, round_[0]):
                #print(f"Semester: {round_[0]}")
                
                sem_id = create_semester(conn, round_[0], "2024")
                
            #Per Session Logic
            elif re.match(ses_format, round_[0]):
                #print(f"Session: {round_[0]}")
                
                ses_id = create_session(conn, sem_id, round_[0], [1])
                
                round_count = 1
                
            #Per Round Logic
            else:
                #print(f"Round: {round_}")
                
                round_id = create_round(conn, ses_id, round_count)
                
                round_count += 1
                
                for match in round_:
                    ls = match.split(",")
                    
                    def format_name(name):
                        name = name.lower()
                        name = name.title()
                        return name.strip()
                    
                    first_name1 = format_name(ls[0])                                              
                    last_name1 = format_name(ls[1])
                    p1id = get_pid_from_name(conn, first_name1, last_name1)
                    
                    first_name2 = format_name(ls[2])
                    last_name2 = format_name(ls[3])
                    p2id = get_pid_from_name(conn, first_name2, last_name2)
                    
                    if ls[4].strip() == "1":
                        #player 1 won 
                        record_match(
                            conn,
                            round_id,
                            p1id,
                            p2id,
                            p1id,
                        )
                    elif ls[5].strip() == "1":
                        #player 2 won
                        record_match(
                            conn,
                            round_id,
                            p1id,
                            p2id,
                            p2id,
                        )