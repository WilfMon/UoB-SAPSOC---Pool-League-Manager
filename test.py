def on_view_leaderboard(self):
        
        def on_semester_selected(container, semester="first"):
            
            #self.leaderboard_container_layout.removeWidget(leaderboard_container_sm)
            
            leaderboard_container_sm = container
            
            # decide which semester to display
            if semester == "first": # perform on first call to show most recent semester
                index = len(semester_leaderboard) - 1
                sem = semester_leaderboard[index]
            
            else:
                semester = self.L_select_semester.currentData()
                
                # clean data
                data = semester.split()
                data.pop(1)
                data.reverse()
                
                for i, sem in enumerate(semester_leaderboard):
                    if int(sem[-1][0]) == int(data[0]): # check if semester_id matches
                        break
                    
            # combo box
            self.L_select_semester = QComboBox()
            
            for semester_ in semester_leaderboard:
                # pass all data but only display the semester year and number
                year_num = str(semester_[-1][1]).split(".")
                
                self.L_select_semester.addItem(f"{year_num[0]} Semester: {year_num[1]}", str(semester_[-1][1]) + " - " + str(semester_[-1][0]))
            
            if semester == "first": # perform on first call to show most recent session
                self.L_select_semester.setCurrentIndex(len(semester_leaderboard) - 1)
            else:     
                self.L_select_semester.setCurrentIndex(i) # set index found earlier
                
            self.L_select_semester.currentIndexChanged.connect(on_semester_selected)
            leaderboard_container_layout_sm.addWidget(self.L_select_semester, 0, 1, alignment=Qt.AlignLeft | Qt.AlignTop)
                    
            sem.pop(-1) # remove data carrying part of the list
            
            leaderboard_container_sm = construct(sem, leaderboard_container_sm)
            self.leaderboard_container_layout.addWidget(leaderboard_container_sm, 0, 0)
                                
            self.L_semester_label = QLabel("Semester Leaderboard:", self)
            leaderboard_container_layout_sm.addWidget(self.L_semester_label, 0, 0, alignment=Qt.AlignLeft | Qt.AlignTop)

            self.L_select_semester_score = QLabel("Points:", self)
            self.L_select_semester_score.setStyleSheet("font-weight: normal;")
            leaderboard_container_layout_sm.addWidget(self.L_select_semester_score, 1, 0, alignment=Qt.AlignLeft | Qt.AlignTop)
            
            self.L_select_semester_name = QLabel("Name:", self)
            self.L_select_semester_name.setStyleSheet("font-weight: normal;")
            leaderboard_container_layout_sm.addWidget(self.L_select_semester_name, 1, 1, alignment=Qt.AlignLeft | Qt.AlignTop)
            
            return leaderboard_container_sm
            
        def on_session_selected(container, session="first"):
            
            #self.leaderboard_container_layout.removeWidget(leaderboard_container_se)

            leaderboard_container_se = container

            # decide which session to display
            if session == "first": # perform on first call to show most recent session
                index = len(session_leaderboard) - 1
                ses = session_leaderboard[index]
            
            else:
                session = self.L_select_session.currentData()
                
                # clean data
                data = session.split()
                data.pop(1)
                data.pop(2)
                
                for i, ses in enumerate(session_leaderboard):
                    if int(ses[-1][0]) == int(data[0]) and int(ses[-1][3]) == int(data[2]): # check if session_id and semester_id matches
                        break
                
            # combo box
            self.L_select_session = QComboBox()
            
            for session_ in session_leaderboard:
                # pass all data but only display the date of the session
                self.L_select_session.addItem(str(session_[-1][1]), str(session_[-1][0]) + " - " + str(session_[-1][1]) + " - " + str(session_[-1][3]))
            
            if session == "first": # perform on first call to show most recent session
                self.L_select_session.setCurrentIndex(len(session_leaderboard) - 1)
            else:     
                self.L_select_session.setCurrentIndex(i) # set index found earlier
                
            self.L_select_session.currentIndexChanged.connect(on_session_selected)
            leaderboard_container_layout_se.addWidget(self.L_select_session, 0, 1, alignment=Qt.AlignLeft | Qt.AlignTop)
                
            ses.pop(-1) # remove data carrying part of the list
            
            print(leaderboard_container_se)
            
            leaderboard_container_se = construct(ses, leaderboard_container_se)
            self.leaderboard_container_layout.addWidget(leaderboard_container_se, 0, 1)
                
            self.L_session_label = QLabel("Session Leaderboard:", self)
            leaderboard_container_layout_se.addWidget(self.L_session_label, 0, 0, alignment=Qt.AlignLeft | Qt.AlignTop)

            self.L_select_session_score = QLabel("Points:", self)
            self.L_select_session_score.setStyleSheet("font-weight: normal;")
            leaderboard_container_layout_se.addWidget(self.L_select_session_score, 1, 0, alignment=Qt.AlignLeft | Qt.AlignTop)
            
            self.L_select_session_name = QLabel("Name:", self)
            self.L_select_session_name.setStyleSheet("font-weight: normal;")
            leaderboard_container_layout_se.addWidget(self.L_select_session_name, 1, 1, alignment=Qt.AlignLeft | Qt.AlignTop)
        
            return leaderboard_container_se
        
        def alltime():
            self.L_alltime_label = QLabel("All-Time Leaderboard:", self)
            leaderboard_container_layout_at.addWidget(self.L_alltime_label, 0, 0, alignment=Qt.AlignLeft | Qt.AlignTop)
            
            self.L_alltime_label_score = QLabel("Points:", self)
            self.L_alltime_label_score.setStyleSheet("font-weight: normal;")
            leaderboard_container_layout_at.addWidget(self.L_alltime_label_score, 1, 0, alignment=Qt.AlignLeft | Qt.AlignTop)
            
            self.L_alltime_label_name = QLabel("Name:", self)
            self.L_alltime_label_name.setStyleSheet("font-weight: normal;")
            leaderboard_container_layout_at.addWidget(self.L_alltime_label_name, 1, 1, alignment=Qt.AlignLeft | Qt.AlignTop)

            construct(alltime_leaderboard, leaderboard_container_layout_at)
            
        def construct(leaderboard, layout):
            
            for n, player in enumerate(leaderboard, start=1):
                n *= 2
                
                line = QFrame()
                line.setFrameShape(QFrame.HLine)
                line.setFrameShadow(QFrame.Sunken)
                line.setStyleSheet("background-color: #3d3d3d")
                
                layout.addWidget(line, n, 0, 1, 2)
                
                points = QLabel(f"{player[2]}")
                points.setStyleSheet("font-weight: normal;")
                
                name = QLabel(f"{player[1]}")
                name.setStyleSheet("font-weight: normal;")

                layout.addWidget(points, n + 1, 0)
                layout.addWidget(name, n + 1, 1)
            
            return layout
            
        clear_layout(self.main_layout)
        self.central.setCurrentIndex(0)

        self.menu_bar = remove_menu(self.menu_bar, "Statistics")

        # get leaderboards
        L = Leaderboard()
        semester_leaderboard, session_leaderboard, alltime_leaderboard = L.collect_leaderboards()
        
        # ui setup
        self.leaderboard_area = QScrollArea()
        self.leaderboard_area.setWidgetResizable(True)
        self.leaderboard_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.leaderboard_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.leaderboard_area.setStyleSheet("background-color: #0b0b0b;")
        
        self.leaderboard_container = QWidget()
        self.leaderboard_container_layout = QGridLayout(self.leaderboard_container)
        self.leaderboard_container_layout.setSpacing(35)

        self.leaderboard_area.setWidget(self.leaderboard_container)
        self.main_layout.addWidget(self.leaderboard_area, 1, 1)
        
        leaderboard_container_sm = QFrame()
        leaderboard_container_sm.setStyleSheet("background-color: #1f1f1f;")
        leaderboard_container_layout_sm = QGridLayout(leaderboard_container_sm)
        
        leaderboard_container_se = QFrame()
        leaderboard_container_se.setStyleSheet("background-color: #1f1f1f;")
        leaderboard_container_layout_se = QGridLayout(leaderboard_container_se)
        
        leaderboard_container_at = QFrame()
        leaderboard_container_at.setStyleSheet("background-color: #1f1f1f;")
        leaderboard_container_layout_at = QGridLayout(leaderboard_container_at)
                        
        alltime()
        
        leaderboard_container_sm = on_semester_selected(leaderboard_container_sm)
        leaderboard_container_se = on_session_selected(leaderboard_container_se)
        
        self.leaderboard_container_layout.addWidget(leaderboard_container_sm, 0, 0)
        self.leaderboard_container_layout.addWidget(leaderboard_container_se, 0, 1)
        self.leaderboard_container_layout.addWidget(leaderboard_container_at, 0, 2)