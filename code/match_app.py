from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QApplication, QFileDialog, QToolTip, QGroupBox, QPushButton, QGridLayout, QMessageBox, QLabel, QButtonGroup, QRadioButton)
from PyQt5.QtGui import QFont
import sqlite3, platform, sys, os, re
import pandas as pd
import numpy as np

class LeaderMatch(QWidget):
    def __init__(self):
        super().__init__()
        self.test_os()
        self.db_path = None
        self.initUI()

    def test_os(self):
        system = platform.system()
        if system == 'Windows':
            self.init_dir = 'C:\\Documents\\'
        else:
            self.init_dir = os.path.expanduser('~/Documents/')

    def get_db_fp(self):
        self.db_path, _ = QFileDialog.getOpenFileName(self,
                                                      caption='Select database file',
                                                      directory=self.init_dir,
                                                      filter='database files(*.db)')
        if self.db_path is not None:
            self.load_initial_values()
            
    def get_values(self):
        if self.i < self.nrow:
            self.a_leader = self.get_arch_leader(self.match_tmp['archid'].iloc[self.i])
            if not np.isnan(self.match_tmp['m1id'].iloc[self.i]):
                v1_leader = self.get_vdem_leader(self.match_tmp['m1id'].iloc[self.i])
                v1_pct = int(self.match_tmp['m1pct'].iloc[self.i])
            else:
                v1_leader, v1_pct = None, None
            if not np.isnan(self.match_tmp['m2id'].iloc[self.i]):
                v2_leader = self.get_vdem_leader(self.match_tmp['m2id'].iloc[self.i])
                v2_pct = int(self.match_tmp['m2pct'].iloc[self.i])
            else:
                v2_leader, v2_pct = None, None
            if not np.isnan(self.match_tmp['m3id'].iloc[self.i]):
                m3_leader = self.get_vdem_leader(self.match_tmp['m3id'].iloc[self.i])
                m3_pct = int(self.match_tmp['m3pct'].iloc[self.i])
            else:
                m3_leader, m3_pct = None, None
            # wrap it all up into something nice:
            self.vdem_leaders = [v1_leader, v2_leader, m3_leader]
            self.pcts = [v1_pct, v2_pct, m3_pct]
        else:
            self.a_leader, self.vdem_leaders, self.pcts = None, [None, None, None], [None, None, None]
            
    def load_initial_values(self):
        self.get_index()
        with sqlite3.connect(self.db_path) as conn:
            self.match_tmp = pd.read_sql_query('SELECT * FROM matches', conn)
        self.nrow = self.match_tmp.shape[0]
        self.get_values()
        a_in = self.format_arch(self.a_leader)
        self.a.setText(a_in)
        v_ins = [self.format_vdem(lead, pct) for lead, pct in zip(self.vdem_leaders, self.pcts)]
        self.v1_box.setText(v_ins[0])
        self.v2_box.setText(v_ins[1])
        self.v3_box.setText(v_ins[2])
        # Try to set the previous match
        if self.a_leader is not None:
            self.get_previous_choice(int(self.a_leader['archid'][0]))
            if self.prev_leader is not None:
                p_in = self.format_vdem(self.prev_leader)
                self.p.setText(p_in)
        else:
            self.p.setText('')

    def format_vdem(self, leader, pct=None):
        if leader is not None:
            vl = leader.drop(axis=1, columns=['vdid'])
            vl.rename(columns={'lname': 'Name',
                               'cname': 'Country',
                               'ltype': 'Leader type',
                               'entry_date': 'Entry Date',
                               'exit_date': 'Exit Date'},
                      inplace=True)
            vlt = vl.T.to_string(header=False)
            vlt = re.sub(r'\n', '<br>', vlt)
            vlt = re.sub(r'(^|<br>)(.*?)\s{2,}', r'\1<b>\2</b>: ', vlt)
            vlt = re.sub(r'</b>:\s+', '</b>:          ', vlt)
            if pct is not None:
                vlt = '<b>' + str(pct) + '%</b><br>' + vlt
            return vlt
        else:
            return ''

    def format_arch(self, leader):
        if leader is not None:
            ar = leader.drop(axis=1, columns=['archid'])
            ar.rename(columns={'lname': 'Name',
                               'cname': 'Country',
                               'entry_date': 'Entry Date',
                               'exit_date': 'Exit Date', 
                               'birth_year': 'Born',
                               'death_year': 'Died'},
                      inplace=True)
            art = ar.T.to_string(header=False)
            art = re.sub(r'\n', '<br>', art)
            art = re.sub(r'(^|<br>)(.*?)\s{2,}', r'\1<b>\2</b>: ', art)
            art = re.sub(r'</b>:\s+', '</b>:          ', art)
            return art
        else:
            return ''

    def get_index(self):
        # a function to get the current index from the database
        with sqlite3.connect(self.db_path) as conn:
            idx = pd.read_sql_query('SELECT i FROM idx WHERE identifier=0', conn)
        self.i = int(idx['i'][0])

    def write_index(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('UPDATE idx SET i = ? WHERE identifier=0', (self.i, ))

    def get_vdem_leader(self, vdid):
        sql = 'SELECT * FROM vdem WHERE vdid = %i' %vdid
        with sqlite3.connect(self.db_path) as conn:
            res = pd.read_sql_query(sql, conn)
        return res

    def get_arch_leader(self, archid):
        sql = 'SELECT * FROM arch WHERE archid = %i' %int(archid)
        with sqlite3.connect(self.db_path) as conn:
            res = pd.read_sql_query(sql, conn)
        return res

    def export_matched(self):
        if self.db_path is not None:
            sql = 'SELECT * FROM results'
            with sqlite3.connect(self.db_path) as conn:
                m = pd.read_sql_query(sql, conn)
            exp_dir = QFileDialog.getExistingDirectory(self,
                                                       directory=self.init_dir,
                                                       caption="Select destination to save matched codes")
            fp = str(exp_dir) + '/matched_leader_codes.csv'
            m.to_csv(fp)
        else:
            alert = QMessageBox()
            alert.setText('You must first set a database!')
            alert.exec_()

    def export_unmatched(self):
        if self.db_path is not None:
            sql_vdem = 'SELECT * FROM vdem WHERE vdid NOT IN (SELECT vdid FROM results)'
            sql_arch = 'SELECT * FROM arch WHERE archid NOT IN (SELECT archid FROM results)'
            with sqlite3.connect(self.db_path) as conn:
                m1 = pd.read_sql_query(sql_vdem, conn)
            with sqlite3.connect(self.db_path) as conn:
                m2 = pd.read_sql_query(sql_arch, conn)
            exp_dir = QFileDialog.getExistingDirectory(self,
                                                       directory=self.init_dir,
                                                       caption="Select destination to save unmatched V-dem codes")
            fp_vdem = str(exp_dir) + '/unmatched_vdem_data.csv'
            fp_arch = str(exp_dir) + '/unmatched_archigos_data.csv'
            m1.to_csv(fp_vdem)
            m2.to_csv(fp_arch)
        else:
            alert = QMessageBox()
            alert.setText('You must first set a database!')
            alert.exec_()
            
    def assign_id(self, vdid, archid):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""INSERT INTO results (vdid, archid) 
                            VALUES (?, ?)
                            ON CONFLICT (archid)
                            DO UPDATE SET vdid = excluded.vdid""", (vdid, archid))

    def detect_button(self):
        if self.v1_button.isChecked():
            return 0
        elif self.v2_button.isChecked():
            return 1
        elif self.v3_button.isChecked():
            return 2
        else:
            return 3

    def select_and_advance(self):
        # This is a function to get a selection from the radio button, write the choice, and advance
        # Get the selection
        sel = self.detect_button()
        # If a value has been selected, write it to file
        if sel <= 2:
            archid = int(self.a_leader['archid'][0])
            vdid = int(self.vdem_leaders[sel]['vdid'][0])
            self.assign_id(vdid, archid)
        else:
            # delete previously written code (if it exists)
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('DELETE FROM results WHERE archid = ?',
                             (int(self.a_leader['archid'][0]), ))
        # advance the counter
        self.i += 1
        self.write_index()
        # get new values
        self.get_values()
        # and display a new one
        a_in = self.format_arch(self.a_leader)
        self.a.setText(a_in)
        v_ins = [self.format_vdem(lead, pct) for lead, pct in zip(self.vdem_leaders, self.pcts)]
        self.v1_box.setText(v_ins[0])
        self.v2_box.setText(v_ins[1])
        self.v3_box.setText(v_ins[2])
        # Try to set the previous match
        if self.a_leader is not None:
            self.get_previous_choice(int(self.a_leader['archid'][0]))
            if self.prev_leader is not None:
                p_in = self.format_vdem(self.prev_leader)
                self.p.setText(p_in)
        else:
            self.p.setText('')
        # And reset the radio button
        self.reset_radio_buttons()

    def reset_radio_buttons(self):
        self.v1_button.setCheckable(False)
        self.v2_button.setCheckable(False)
        self.v3_button.setCheckable(False)
        self.v4_button.setCheckable(False)
        self.v1_button.setChecked(False)
        self.v2_button.setChecked(False)
        self.v3_button.setChecked(False)
        self.v4_button.setChecked(False)
        self.v1_button.setCheckable(True)
        self.v2_button.setCheckable(True)
        self.v3_button.setCheckable(True)
        self.v4_button.setCheckable(True)
        
    def back_index(self):
        # a function to move the index back one
        if self.i >= 1:
            self.i -= 1
            self.write_index()
            # get new values
            self.get_values()
            # and display a new one
            a_in = self.format_arch(self.a_leader)
            self.a.setText(a_in)
            v_ins = [self.format_vdem(lead, pct) for lead, pct in zip(self.vdem_leaders, self.pcts)]
            self.v1_box.setText(v_ins[0])
            self.v2_box.setText(v_ins[1])
            self.v3_box.setText(v_ins[2])
            # Try to set the previous match
            self.get_previous_choice(int(self.a_leader['archid'][0]))
            if self.prev_leader is not None:
                p_in = self.format_vdem(self.prev_leader)
                self.p.setText(p_in)
            else:
                self.p.setText('')
        else:
            alert = QMessageBox()
            alert.setText('Cannot go back further.')
            alert.exec_()

    def get_previous_choice(self, archid):
        sql = 'SELECT * FROM vdem WHERE vdid = (SELECT vdid FROM results WHERE archid = %i)' %archid
        with sqlite3.connect(self.db_path) as conn:
            res = pd.read_sql_query(sql, conn)
        if res.shape[0] > 0:
            self.prev_leader = res
            vdid = res['vdid'][0]
            id_tests = [vdid in x['vdid'].unique() for x in self.vdem_leaders]
            try:
                vdem_index = id_tests.index(True)
            except ValueError:
                vdem_index = None
            if vdem_index == 0:
                self.v1_button.setChecked(True)
            elif vdem_index == 1:
                self.v2_button.setChecked(True)
            elif vdem_index == 2:
                self.v3_button.setChecked(True)
            else:
                self.v4_button.setChecked(True)            
        else:
            self.prev_leader = None
            self.reset_radio_buttons()
            

    def initUI(self):
        # Basic definitions
        QToolTip.setFont(QFont('SansSerif', 10))
            
        # Create all of the objects
        ### Left column box
        self.left_col_box = QGroupBox("Menu")

        # Define the buttons
        load_button = QPushButton('Load Database', self)
        load_button.setToolTip('Start here to load the database file and begin matching.')
        load_button.clicked.connect(self.get_db_fp)

        exp_match_button = QPushButton('Export Matched Codes', self)
        exp_match_button.setToolTip('Export a csv of the matched codes.')
        exp_match_button.clicked.connect(self.export_matched)

        exp_unmatch_button = QPushButton('Export Unmatched Codes', self)
        exp_unmatch_button.setToolTip('Export csv files of the unmatched data')
        exp_unmatch_button.clicked.connect(self.export_unmatched)

        exit_button = QPushButton('Exit', self)
        exit_button.setToolTip('Exit program')
        exit_button.clicked.connect(QApplication.instance().quit)

        # Layout the buttons
        lcol_layout = QVBoxLayout()
        lcol_layout.addWidget(load_button)
        # lcol_layout.addWidget(start_button)
        lcol_layout.addWidget(exp_match_button)
        lcol_layout.addWidget(exp_unmatch_button)
        lcol_layout.addWidget(exit_button)
        lcol_layout.addStretch(1)
        self.left_col_box.setLayout(lcol_layout)

        ### Arch box
        self.arch_box = QGroupBox("Archigos Leader")
        self.a = QLabel(self)
        self.a.setTextFormat(Qt.RichText)
        self.a.setText('')

        # layout the box
        arch_layout = QGridLayout()
        arch_layout.addWidget(self.a, 0, 0)
        self.arch_box.setLayout(arch_layout)

        ### Previous match box
        self.prev_box = QGroupBox("Previous Match")
        self.p = QLabel(self)
        self.p.setTextFormat(Qt.RichText)
        self.p.setText('')

        # layout the box
        prev_layout = QGridLayout()
        prev_layout.addWidget(self.p, 0, 0)
        self.prev_box.setLayout(prev_layout)
        
        ### Directions box
        self.directions_box = QGroupBox("Keybindings and Help")

        # Define the directions stuff
        kb = QLabel()
        kb.setTextFormat(Qt.RichText)
        kb.setWordWrap(True)
        kb.setText("""Directions<br>
                      Start by loading the match database file using the button on the left. Then match leaders as they appear. You may use the keybindings below or select with the mouse. Next will save your selection automatically and advance to the next leader. Undo will move backwards in the list (infinitely and across sessions) and will display the previous selection. If none of the leaders appear to be correct, then select option 4 (none of these). <br><br>
                      Keybindings:<br>
                      <b>Number</b> keys can be used to select the leaders (e.g. 1-4) <br>
                      <b>enter</b> advances to the next leader (same as 'next')<br>
                      <b>backspace</b> moves to the previous leader (same as 'undo')<br>
                      <b>escape</b> exits the program<br>""")

        # layout the box
        directions_layout = QGridLayout()
        directions_layout.addWidget(kb, 0, 0)
        self.directions_box.setLayout(directions_layout)
        
        ### V-Dem leaders box
        self.vdem_box = QGroupBox("Leader Matches")
        self.v1_box = QLabel()
        self.v1_box.setTextFormat(Qt.RichText)
        self.v1_box.setText('')
        self.v2_box = QLabel()
        self.v2_box.setTextFormat(Qt.RichText)
        self.v2_box.setText('')
        self.v3_box = QLabel()
        self.v3_box.setTextFormat(Qt.RichText)
        self.v3_box.setText('')

        # layout the box
        vdem_layout = QHBoxLayout()
        vdem_layout.addWidget(self.v1_box)
        vdem_layout.addWidget(self.v2_box)
        vdem_layout.addWidget(self.v3_box)
        self.vdem_box.setLayout(vdem_layout)

        ### Options to select correct leader
        self.opts = QGroupBox()

        # Define the button
        self.v1_button = QRadioButton('Leader 1', self)
        self.v2_button = QRadioButton('Leader 2', self)
        self.v3_button = QRadioButton('Leader 3', self)
        self.v4_button = QRadioButton('None of these', self)

        # layout
        opts_layout = QHBoxLayout()
        opts_layout.addWidget(self.v1_button)
        opts_layout.addWidget(self.v2_button)
        opts_layout.addWidget(self.v3_button)
        opts_layout.addWidget(self.v4_button)
        self.opts.setLayout(opts_layout)

        ### Accept/next box
        self.accept = QGroupBox() 

        # Define the button
        accept_button = QPushButton('Accept', self)
        accept_button.setToolTip('Accept selected leader and advance')
        accept_button.clicked.connect(self.select_and_advance)

        # Layout the button
        accept_layout = QGridLayout()
        accept_layout.addWidget(accept_button)
        self.accept.setLayout(accept_layout)
        
        self.back = QGroupBox()

        # Define the button
        back_button = QPushButton('Undo!', self)
        back_button.setToolTip('Move backwards in the leader list')
        back_button.clicked.connect(self.back_index)

        # Layout the button
        back_layout = QGridLayout()
        back_layout.addWidget(back_button)
        self.back.setLayout(back_layout)                

        # Generate the main layout
        main_layout = QGridLayout()
        main_layout.addWidget(self.left_col_box, 0, 0, 4, 1)
        main_layout.addWidget(self.arch_box, 0, 1, 4, 1)
        main_layout.addWidget(self.prev_box, 0, 2, 4, 1)
        main_layout.addWidget(self.directions_box, 0, 3, 4, 3)
        main_layout.addWidget(self.vdem_box, 5, 1, 4, 4)
        main_layout.addWidget(self.opts, 9, 1, 1, 4)
        main_layout.addWidget(self.accept, 10, 1, 1, 1)
        main_layout.addWidget(self.back, 10, 4, 1, 1)
        main_layout.setRowStretch(0, 1)
        main_layout.setRowStretch(1, 1)
        main_layout.setRowStretch(1, 2)
        main_layout.setRowStretch(1, 3)
        self.setLayout(main_layout)
        
        # Last things to do 
        self.setGeometry(300, 300, 1050, 700) # will need to change this
        self.setWindowTitle('Archigos/V-Dem Leader Matching')
        self.show()

    ### Keybindings Time
    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.save_and_exit()
        elif e.key() == Qt.Key_Enter or e.key() == Qt.Key_Return:
            self.select_and_advance()
        elif e.key() == Qt.Key_Backspace:
            self.back_index()
        elif e.key() == Qt.Key_1:
            self.v1_button.setChecked(True)
        elif e.key() == Qt.Key_2:
            self.v2_button.setChecked(True)
        elif e.key() == Qt.Key_3:
            self.v3_button.setChecked(True)
        elif e.key() == Qt.Key_4:
            self.v4_button.setChecked(True)

    def save_and_exit(self):
        if self.db_path is not None:
            self.write_index()
        self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    lm = LeaderMatch()
    sys.exit(app.exec_())
