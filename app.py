import os
import sqlite3
import tkinter as tk
import tkinter.messagebox as mb
import tkinter.simpledialog as sd
import tkinter.ttk as ttk

db = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'library.db'))
db.execute('CREATE TABLE IF NOT EXISTS Library (BK_NAME TEXT, BK_ID TEXT PRIMARY KEY NOT NULL, '
           'AUTHOR_NAME TEXT, BK_STATUS TEXT, CARD_ID TEXT)')


def run(sql, *args):
    db.execute(sql, args)
    db.commit()


def issuer_card():
    """Ask for the issuer's card ID; returns '' if empty or cancelled."""
    cid = (sd.askstring('Issuer Card ID', "What is the Issuer's Card ID?\t\t\t") or '').strip()
    if not cid:
        mb.showerror('Issuer ID required', "Can't keep Issuer ID empty, it must have a value")
    return cid


def card_for_status():
    return 'N/A' if bk_status.get() == 'Available' else issuer_card()


def selected():
    """Book ID of the selected row (the row's iid), or '' after showing an error."""
    iid = tree.focus()
    if not iid:
        mb.showerror('Select a row!', 'Please select a record in the table first.')
    return iid


def display_records():
    tree.delete(*tree.get_children())
    for rec in db.execute('SELECT * FROM Library'):
        tree.insert('', tk.END, iid=rec[1], values=rec)  # iid keeps IDs like "007" intact


def clear_fields():
    bk_status.set('Available')
    for var in (bk_name, bk_id, author_name):
        var.set('')
    bk_id_entry.config(state='normal')
    clear.config(state='normal')
    edit.place_forget()
    tree.selection_remove(tree.selection())


def clear_and_display():
    clear_fields()
    display_records()


def add_record():
    if not bk_id.get().strip():
        return mb.showerror('Book ID required', 'Book ID cannot be empty.')
    card = card_for_status()
    if not card or not mb.askyesno('Are you sure?', 'Are you sure this is the data you want to enter?\n'
                                   'Please note that Book ID cannot be changed in the future'):
        return
    try:
        run('INSERT INTO Library VALUES (?, ?, ?, ?, ?)',
            bk_name.get(), bk_id.get().strip(), author_name.get(), bk_status.get(), card)
    except sqlite3.IntegrityError:
        return mb.showerror('Book ID already in use!', 'That Book ID is already in the database.')
    clear_and_display()
    mb.showinfo('Record added', 'The new record was successfully added to your database')


def view_record():
    iid = selected()
    if iid:
        name, _, author, status, _ = db.execute('SELECT * FROM Library WHERE BK_ID=?', (iid,)).fetchone()
        bk_name.set(name or '')
        bk_id.set(iid)
        author_name.set(author or '')
        bk_status.set(status)
    return iid


def save_update():
    card = card_for_status()
    if card:
        run('UPDATE Library SET BK_NAME=?, BK_STATUS=?, AUTHOR_NAME=?, CARD_ID=? WHERE BK_ID=?',
            bk_name.get(), bk_status.get(), author_name.get(), card, bk_id.get())
        clear_and_display()


def update_record():
    if view_record():
        bk_id_entry.config(state='disabled')
        clear.config(state='disabled')
        edit.place(x=50, y=375)


def remove_record():
    iid = selected()
    if iid:
        run('DELETE FROM Library WHERE BK_ID=?', iid)
        clear_and_display()
        mb.showinfo('Done', 'The record was successfully deleted.')


def delete_inventory():
    if mb.askyesno('Are you sure?', 'Are you sure you want to delete the entire inventory?\n\n'
                   'This command cannot be reversed'):
        run('DELETE FROM Library')
        clear_and_display()


def change_availability():
    iid = selected()
    if not iid:
        return
    if tree.set(iid, 'Status') == 'Issued':
        if not mb.askyesno('Is return confirmed?', 'Has the book been returned to you?'):
            return mb.showinfo('Cannot be returned',
                               'The book status cannot be set to Available unless it has been returned')
        run('UPDATE Library SET BK_STATUS=?, CARD_ID=? WHERE BK_ID=?', 'Available', 'N/A', iid)
    else:
        card = issuer_card()
        if not card:
            return
        run('UPDATE Library SET BK_STATUS=?, CARD_ID=? WHERE BK_ID=?', 'Issued', card, iid)
    clear_and_display()


# GUI
LF_BG, RTF_BG, RBF_BG, BTN_BG = 'LightSkyBlue', 'DeepSkyBlue', 'DodgerBlue', 'SteelBlue'
LBL_FONT, ENTRY_FONT, BTN_FONT = ('Georgia', 13), ('Times New Roman', 12), ('Gill Sans MT', 13)
TITLE_FONT = ('Noto Sans CJK TC', 15, 'bold')

root = tk.Tk()
root.title('Library Management System')
root.geometry('1010x530')
root.resizable(False, False)

tk.Label(root, text='LIBRARY MANAGEMENT SYSTEM', font=TITLE_FONT, bg=BTN_BG, fg='White').pack(side=tk.TOP, fill=tk.X)

bk_status, bk_name, bk_id, author_name = (tk.StringVar() for _ in range(4))

left_frame = tk.Frame(root, bg=LF_BG)
left_frame.place(x=0, y=30, relwidth=0.3, relheight=0.96)
RT_frame = tk.Frame(root, bg=RTF_BG)
RT_frame.place(relx=0.3, y=30, relheight=0.2, relwidth=0.7)
RB_frame = tk.Frame(root)
RB_frame.place(relx=0.3, rely=0.24, relheight=0.785, relwidth=0.7)

for label, x, y, var in (('Book Name', 98, 25, bk_name), ('Book ID', 110, 105, bk_id),
                         ('Author Name', 90, 185, author_name)):
    tk.Label(left_frame, text=label, bg=LF_BG, font=LBL_FONT).place(x=x, y=y)
    entry = tk.Entry(left_frame, width=25, font=ENTRY_FONT, textvariable=var)
    entry.place(x=45, y=y + 30)
    if var is bk_id:
        bk_id_entry = entry

tk.Label(left_frame, text='Status of the Book', bg=LF_BG, font=LBL_FONT).place(x=75, y=265)
dd = tk.OptionMenu(left_frame, bk_status, 'Available', 'Issued')
dd.configure(font=ENTRY_FONT, width=12)
dd.place(x=75, y=300)


def button(parent, text, command, width=20):
    return tk.Button(parent, text=text, font=BTN_FONT, bg=BTN_BG, width=width, command=command)


button(left_frame, 'Add new record', add_record).place(x=50, y=375)
clear = button(left_frame, 'Clear fields', clear_fields)
clear.place(x=50, y=435)
edit = button(left_frame, 'Update Record', save_update)  # shown over "Add" only while updating

for text, command, x, width in (('Delete book record', remove_record, 8, 17),
                                ('Delete full inventory', delete_inventory, 178, 17),
                                ('Update book details', update_record, 348, 17),
                                ('Change Book Availability', change_availability, 518, 19)):
    button(RT_frame, text, command, width).place(x=x, y=30)

tk.Label(RB_frame, text='BOOK INVENTORY', bg=RBF_BG, font=TITLE_FONT).pack(side=tk.TOP, fill=tk.X)

COLUMNS = (('Book Name', 'Book Name', 225), ('Book ID', 'Book ID', 70), ('Author', 'Author', 150),
           ('Status', 'Status of the Book', 105), ('Issuer Card ID', 'Card ID of the Issuer', 132))
tree = ttk.Treeview(RB_frame, selectmode=tk.BROWSE, show='headings', columns=[c[0] for c in COLUMNS])
for col, heading, width in COLUMNS:
    tree.heading(col, text=heading, anchor=tk.CENTER)
    tree.column(col, width=width, stretch=False)

xbar = tk.Scrollbar(tree, orient=tk.HORIZONTAL, command=tree.xview)
ybar = tk.Scrollbar(tree, orient=tk.VERTICAL, command=tree.yview)
xbar.pack(side=tk.BOTTOM, fill=tk.X)
ybar.pack(side=tk.RIGHT, fill=tk.Y)
tree.config(xscrollcommand=xbar.set, yscrollcommand=ybar.set)
tree.place(y=30, x=0, relheight=0.9, relwidth=1)

clear_and_display()
root.mainloop()
