# Standard libraries
import csv
import datetime
import os
import re
import shutil
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk
import pandas as pd
import subprocess

# Third-party libraries
import cv2
from PIL import Image, ImageTk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.backends.backend_pdf
from matplotlib.figure import Figure
from tkcalendar import DateEntry
import mplcursors
import babel.numbers

# Define the path of the destination CSV file
csv_file = "Car_plates.csv"

# Define the path of the Drivers photo
destination_folder = "Drivers/"

# Create the destination folder if it does not exist
if not os.path.exists(destination_folder):
    os.makedirs(destination_folder)

# Create a global variable
driver_picture_path = None
driver_picture = None
driver_photo = None
picture_display = None
car_plate_entry = None
car_plate_type_combobox = None
current_car_plate = None
validity_label = None


# Define function to run Detection
def run_exe():
    subprocess.Popen(["Detect.exe"])


# Define a function for Add Car Plate side window
def create_add_window():
    global add_window, picture_display, car_plate_type_combobox, car_plate_entry, id_entry

    # Check if the add_window already exists
    close_side_window()  # Destroy the existing add_window

    # Create a new Toplevel window
    add_window = tk.Toplevel(window)
    add_window.geometry("550x500")
    add_window.title("Add Car Plate")

    # Set the add_window as a transient window of the main window
    add_window.transient(window)

    # Override the default close window behavior
    add_window.protocol("WM_DELETE_WINDOW", confirm_exit)

    # Create a label and an entry field for the ID
    id_label = tk.Label(add_window, text="ID:")
    id_label.grid(row=0, column=0, padx=10, pady=10, sticky="e")
    id_entry = tk.Entry(add_window)
    id_entry.grid(row=0, column=1, padx=10, pady=10, sticky="w")

    # Create a label and an entry field for the car plate number
    car_plate_label = tk.Label(add_window, text="Car Plate Number:")
    car_plate_label.grid(row=0, column=2, padx=10, pady=10, sticky="e")
    car_plate_entry = tk.Entry(add_window)
    car_plate_entry.grid(row=0, column=3, padx=10, pady=10, sticky="w")

    # Create a combobox with the car plate type options
    car_plate_type_options = ["Staff", "Student"]

    # Add a label for the combobox
    car_plate_type_label = tk.Label(add_window, text="Position:")
    car_plate_type_label.grid(row=1, column=0, padx=10, pady=10, sticky="e")

    car_plate_type_combobox = ttk.Combobox(add_window, values=car_plate_type_options, state="readonly")
    car_plate_type_combobox.grid(row=1, column=1, padx=10, pady=10, sticky="w", columnspan=3)

    # Create a button to select the driver picture
    select_button = tk.Button(add_window, text="Select Driver Picture", command=select_driver_picture)
    select_button.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

    # Create a button to add the car plate number to the CSV file
    add_button = tk.Button(add_window, text="Add Car Plate", command=add_car_plate)
    add_button.grid(row=2, column=2, columnspan=2, padx=10, pady=10)

    # Create a label for the driver picture
    picture_label = tk.Label(add_window, text="Driver Picture:")
    picture_label.grid(row=3, column=0, columnspan=4, padx=10, pady=10)

    # Create an empty PhotoImage object
    driver_picture = tk.PhotoImage()

    # Create an Image widget to display the driver picture
    picture_display = tk.Label(add_window, image=driver_picture)
    picture_display.grid(row=4, column=0, columnspan=4, padx=10, pady=10)

    # Update the window and center it
    add_window.update()
    center_window(add_window)


# Define a function to add a car plate number to the CSV file
def add_car_plate():
    global driver_picture_path, id_entry, add_window

    # Check if the user has selected a driver photo
    if not driver_picture_path:
        messagebox.showerror("Error", "Please select a driver photo.")
        return

    # Get the selected car plate type
    car_plate_type = car_plate_type_combobox.get()

    # Check if the user has selected a position
    if not car_plate_type:
        messagebox.showerror("Error", "Please select a position.")
        return

    # Calculate the car plate validity date based on the selected position
    if car_plate_type == "Student":
        validity = datetime.date.today() + datetime.timedelta(days=365)
    elif car_plate_type == "Staff":
        validity = datetime.date.today() + datetime.timedelta(days=730)
    else:
        validity = None

    # Get the car plate number entered by the user
    car_plate_num = car_plate_entry.get()

    # Check if the car plate number is empty
    if not car_plate_num:
        messagebox.showerror("Error", "Please enter a car plate number.")
        return

    # Get the entered ID number
    id_num = id_entry.get()

    # Check if the ID number is empty
    if not id_num:
        messagebox.showerror("Error", "Please enter an ID number.")
        return

    # Check if the ID number contains special characters
    if not id_num.isalnum():
        messagebox.showerror("Error", "The ID number can only contain alphanumeric characters.")
        return

    # Check if the ID number exceeds the maximum length
    if len(id_num) > 10:
        messagebox.showerror("Error", "The ID number cannot exceed 10 characters.")
        return

    # Check if the CSV file exists
    file_exists = os.path.exists(csv_file)

    # Get the current number of car plates in the CSV file
    num_car_plates = 0
    car_plate_nums = set()
    id_car_counts = {}
    id_car_positions = {}  # NEW
    header_row = ["ID", "Serial Number", "Car Plate", "Position", "Driver Photo", "Valid Until"]
    if file_exists:
        with open(csv_file, "r") as file:
            reader = csv.reader(file)
            csv_contents = list(reader)
            if len(csv_contents) > 0:
                header_row_csv = csv_contents[0]
                if header_row_csv == header_row:
                    num_car_plates = len(csv_contents) - 1
                    # Create a set of existing car plate numbers
                    car_plate_nums = set([row[2] for row in csv_contents[1:]])
                    # Initialize the dictionary if it doesn't exist or is empty
                    if not id_car_counts:
                        id_car_counts = {row[0]: 0 for row in csv_contents[1:]}
                        id_car_positions = {row[0]: row[3] for row in csv_contents[1:]}  # NEW

                    # Increment the count for each ID
                    for row in csv_contents[1:]:
                        id_car_counts[row[0]] += 1

    # Check if the car plate number is valid
    if len(car_plate_num) > 8:
        messagebox.showerror("Error", "The car plate number cannot be longer than 8 characters.")
        return
    elif not car_plate_num.replace(" ", "").isalnum():
        messagebox.showerror("Error", "The car plate number can only contain letters, numbers, and spaces.")
        return
    elif not any(char.isalpha() for char in car_plate_num):
        messagebox.showerror("Error", "The car plate number must contain at least one letter.")
        return
    elif not any(char.isdigit() for char in car_plate_num):
        messagebox.showerror("Error", "The car plate number must contain at least one digit.")
        return
    elif car_plate_num.upper() in car_plate_nums:
        messagebox.showerror("Error", "The car plate number already exists in the system.")
        return
    elif not re.match(r'^[a-zA-Z]{1,3}\s\d{1,4}$', car_plate_num):
        messagebox.showerror("Error", "The car plate number must be in the format ABC(space)1234.")
        return

    # Convert the car plate number to all capital letters
    car_plate_num = car_plate_num.upper()

    # Check if the ID number has already registered 2 cars
    if id_num in id_car_counts and id_car_counts.get(id_num, 0) >= 2:
        messagebox.showerror("Error", "The ID has already registered the maximum number of cars.")
        return

    # NEW: Check if the ID number already has a different position
    if id_num in id_car_positions and id_car_positions.get(id_num) != car_plate_type:
        messagebox.showerror("Error", "The same ID cannot be registered with a different position.")
        return

    # Check if the CSV file is empty or doesn't contain a header row
    if not file_exists or (num_car_plates == 0 and header_row_csv != header_row):
        with open(csv_file, "a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(header_row)

    # Add the car plate number to the CSV file
    with open(csv_file, "a", newline="") as file:
        writer = csv.writer(file)

        # Calculate the next serial number
        if file_exists:
            existing_serials = [row[1] for row in csv_contents[1:] if row[1].startswith('AMC') and row[1][3:].isdigit()]
            max_serial = max(existing_serials, default='AMC000')[3:]
            next_serial = f"AMC{int(max_serial) + 1:03d}"
        else:
            next_serial = "AMC001"

        # Rename the driver photo file
        new_photo_path = os.path.join(destination_folder,
                                      f"{car_plate_num}_driver_photo{os.path.splitext(driver_picture_path)[1]}")
        os.rename(driver_picture_path, new_photo_path)

        # Write the new row to the CSV file with the generated serial number
        writer.writerow(
            [id_num, next_serial, car_plate_num, car_plate_type, os.path.basename(new_photo_path), validity])

        # Clear the entry fields for the next car plate number and ID
        car_plate_entry.delete(0, "end")
        id_entry.delete(0, "end")

        # Reset the combobox selection
        car_plate_type_combobox.set("")

    # Reset the driver_picture and driver_picture_path variables
    driver_picture = tk.PhotoImage()
    driver_picture_path = None
    picture_display.config(image=driver_picture)

    # Display the success message
    messagebox.showinfo("Success", "The new driver registered successfully.")


# Create a function to handle the file select
def select_driver_picture():
    global driver_picture, driver_picture_path, picture_display

    # Set the initial folder path to "Captured Faces"
    initial_folder = "Captured Faces"

    # Open a file dialog to select a driver picture
    filename = filedialog.askopenfilename(initialdir=initial_folder, title="Select Driver Picture",
                                          filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])

    if not filename:
        # If no file is selected, show a warning message and return from the function
        messagebox.showwarning("Warning", "Please select a driver photo.")
        return

    # Check the file size
    file_size = os.path.getsize(filename)
    if file_size > 5 * 1024 * 1024:  # Check if the file size is larger than 5 MB
        messagebox.showerror("Error",
                             "The selected file is too large. Please select a file less than or equal to 5 MB.")
        return

    # Load the selected image into the PhotoImage object
    image = Image.open(filename)
    # Resize the image to fit within the label
    image = image.resize((250, 300), Image.LANCZOS)
    driver_picture = ImageTk.PhotoImage(image)
    # Update the image in the picture_display widget
    picture_display.config(image=driver_picture)
    picture_display.image = driver_picture
    # Update the driver_picture_path variable with the selected file path
    driver_picture_path = filename
    # Display a message box to confirm that the driver picture has been selected
    messagebox.showinfo("Driver Picture Selected", "The driver picture has been selected.")


# Define a side window to create search window
def create_search_window():
    global search_window, car_plate_entry, picture_display, validity_label

    # Check if the search_window already exists
    close_side_window()  # Destroy the existing search_window

    # Create a new Toplevel window
    search_window = tk.Toplevel(window)
    search_window.geometry("600x450")
    search_window.title("Search Car Plate")

    # Set the search_window as a transient window of the main window
    search_window.transient(window)

    # Override the default close window behavior
    search_window.protocol("WM_DELETE_WINDOW", confirm_exit)

    # Create a label and an entry field for the car plate number
    car_plate_label = tk.Label(search_window, text="Car Plate Number:")
    car_plate_label.grid(row=0, column=0, padx=10, pady=10, sticky="e")
    car_plate_entry = tk.Entry(search_window)
    car_plate_entry.grid(row=0, column=1, padx=10, pady=10, sticky="w")

    # Create a label to display the car plate validity
    validity_label = tk.Label(search_window, text="Valid Until:")
    validity_label.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="w")

    # Create a button to search the car plate number in the CSV file
    search_button = tk.Button(search_window, text="Search Car Plate", command=search_car_plate)
    search_button.grid(row=0, column=2, padx=10, pady=10)

    # Create a button to delete the car plate number from the CSV file
    delete_button = tk.Button(search_window, text="Delete Car Plate", command=delete_car_plate)
    delete_button.grid(row=0, column=3, padx=10, pady=10)

    # Create a label for the driver picture
    picture_display = tk.Label(search_window)
    picture_display.grid(row=2, column=0, columnspan=4, padx=10, pady=10)

    center_window(search_window)


# Define a function to search a car plate number
def search_car_plate():
    global picture_display, driver_photo, current_car_plate, update_button

    # Get the car plate number entered by the user
    car_plate_num = car_plate_entry.get().upper()

    # Check if the car plate number is empty
    if not car_plate_num:
        messagebox.showwarning("Warning", "Please enter a car plate number.")
        return

    # Check if the CSV file exists
    file_exists = os.path.exists(csv_file)

    # Get the current number of car plates in the CSV file
    if file_exists:
        with open(csv_file, "r") as file:
            reader = csv.reader(file)
            csv_contents = list(reader)
            if len(csv_contents) > 0:
                # Search for the car plate number in the CSV file
                found = False
                for row in csv_contents[1:]:
                    if row[2] == car_plate_num:  # Change from row[1] to row[2]
                        # Display the driver photo
                        driver_photo_path = os.path.join(destination_folder, row[4])  # Change from row[3] to row[4]

                        if os.path.exists(driver_photo_path):
                            driver_photo = Image.open(driver_photo_path)
                        else:
                            # Display a default image or message
                            driver_photo = Image.open("Default.jpg")
                            messagebox.showwarning("Warning", "Driver's photo not found.")

                        driver_photo = driver_photo.resize((250, 300), Image.LANCZOS)
                        driver_photo = ImageTk.PhotoImage(driver_photo)
                        picture_display.config(image=driver_photo)

                        # Display the car plate validity
                        car_plate_validity = row[5]  # Change the index as per your CSV file structure
                        validity_label.config(text=f"Validity: {car_plate_validity}")

                        # Display the driver position
                        driver_position = row[3]  # Change from row[2] to row[3]
                        messagebox.showinfo("Driver Position", f"The driver is a {driver_position}.")

                        # Update the current car plate number
                        current_car_plate = car_plate_num

                        found = True
                        break
                if not found:
                    # Display an error message if the car plate number is not found
                    messagebox.showerror("Error", "The car plate number is not found.")
                    return
            else:
                # Display an error message if the CSV file is empty
                messagebox.showerror("Error", "The CSV file is empty.")
                return
    else:
        # Display an error message if the CSV file does not exist
        messagebox.showerror("Error", "The CSV file does not exist.")

    # Create a button to update the validity date
    update_button = tk.Button(search_window, text="Update Validity", command=update_validity)
    update_button.grid(row=1, column=2, padx=10, pady=10)


# Define a function to delete a car plate number
def delete_car_plate():
    global current_car_plate

    # Get the current car plate number
    car_plate_num = current_car_plate

    # Check if the car plate number is empty
    if not car_plate_num:
        messagebox.showwarning("Warning", "Please search for a car plate number first.")
        return

    # Ask for confirmation before deletion
    confirm_delete = messagebox.askyesno("Confirmation", "Are you sure you want to delete the car plate number?")
    if not confirm_delete:
        return

    # Check if the CSV file exists
    file_exists = os.path.exists(csv_file)

    # Get the current number of car plates in the CSV file
    if file_exists:
        with open(csv_file, "r") as file:
            reader = csv.reader(file)
            csv_contents = list(reader)
            if len(csv_contents) > 0:
                # Search for the car plate number in the CSV file
                found = False
                for i, row in enumerate(csv_contents[1:], start=1):
                    if row[2] == car_plate_num:
                        # Delete the row from the CSV file
                        del csv_contents[i]

                        # Delete the driver photo file
                        driver_photo_path = os.path.join(destination_folder, row[4])
                        if os.path.exists(driver_photo_path):
                            os.remove(driver_photo_path)

                        # Write the updated contents to the CSV file
                        with open(csv_file, "w", newline="") as write_file:
                            writer = csv.writer(write_file)
                            writer.writerows(csv_contents)

                        # Display the success message
                        messagebox.showinfo("Success", "The car plate number has been deleted.")

                        # Clear the current car plate number and image
                        current_car_plate = ""
                        picture_display.config(image="")

                        found = True
                        break

                # If car plate number is not found, show error after checking all rows
                if not found:
                    messagebox.showerror("Error", "The car plate number is not found.")
            else:
                # Display an error message if the CSV file is empty
                messagebox.showerror("Error", "The CSV file is empty.")
    else:
        # Display an error message if the CSV file does not exist
        messagebox.showerror("Error", "The CSV file does not exist.")

    # Clear the entry field for the next car plate number
    car_plate_entry.delete(0, "end")


# Define a function to update car plate validity
def update_validity():
    global current_car_plate

    # Get the current car plate number
    car_plate_num = current_car_plate

    # Check if the car plate number is empty
    if not car_plate_num:
        messagebox.showwarning("Warning", "Please search for a car plate number first.")
        return

    # Ask for confirmation before updating
    confirm_update = messagebox.askyesno("Confirmation", "Are you sure you want to update the validity date?")
    if not confirm_update:
        return

    # Check if the CSV file exists
    file_exists = os.path.exists(csv_file)

    # Get the current number of car plates in the CSV file
    if file_exists:
        with open(csv_file, "r") as file:
            reader = csv.reader(file)
            csv_contents = list(reader)
            if len(csv_contents) > 0:
                # Search for the car plate number in the CSV file
                found = False
                for i, row in enumerate(csv_contents[1:], start=1):
                    if row[2] == car_plate_num:
                        # Get the driver's position
                        driver_position = row[3]

                        # Calculate the new validity date based on the driver's position
                        if driver_position == "Student":
                            new_validity = (datetime.date.today() + datetime.timedelta(days=365)).isoformat()
                        elif driver_position == "Staff":
                            new_validity = (datetime.date.today() + datetime.timedelta(days=730)).isoformat()
                        else:
                            new_validity = None

                        # Update the validity date in the CSV file
                        csv_contents[i][5] = new_validity

                        # Write the updated contents to the CSV file
                        with open(csv_file, "w", newline="") as write_file:
                            writer = csv.writer(write_file)
                            writer.writerows(csv_contents)

                        # Update the current car plate number with the new car plate number
                        current_car_plate = car_plate_num

                        # Display the success message
                        messagebox.showinfo("Success", "The validity date has been updated.")

                        # Update the validity label
                        validity_label.config(text=f"Validity: {new_validity}")

                        found = True
                        break

                # If car plate number is not found, show error after checking all rows
                if not found:
                    messagebox.showerror("Error", "The car plate number is not found.")
            else:
                # Display an error message if the CSV file is empty
                messagebox.showerror("Error", "The CSV file is empty.")
    else:
        # Display an error message if the CSV file does not exist
        messagebox.showerror("Error", "The CSV file does not exist.")


# Define a side window to create advanced window
def create_advanced_window():
    global advanced_window, start_date_entry, end_date_entry, result_tree, export_button, status_combobox

    # Check if the advanced_window already exists
    close_side_window()  # Destroy the existing advanced_window

    # Create a new Toplevel window
    advanced_window = tk.Toplevel(window)
    advanced_window.geometry("600x450")
    advanced_window.title("Advanced Search(Car Entry)")

    # Set the advanced_window as a transient window of the main window
    advanced_window.transient(window)

    # Override the default close window behavior
    advanced_window.protocol("WM_DELETE_WINDOW", confirm_exit)

    # Create a frame for date entries and retrieve button
    top_frame = tk.Frame(advanced_window)
    top_frame.pack(side="top", padx=10, pady=10)

    # Create a frame for the status selection
    status_frame = tk.Frame(advanced_window)
    status_frame.pack(side="top", padx=10, pady=10)

    # Create a label and a combobox for the status selection
    status_label = tk.Label(status_frame, text="Status:")
    status_label.pack(side="left", padx=10, pady=10)

    # Create a label and a DateEntry widget for the start date
    start_date_label = tk.Label(top_frame, text="Start Date:")
    start_date_label.pack(side="left", padx=10, pady=10)
    start_date_entry = DateEntry(top_frame, date_pattern="yyyy-mm-dd", state="readonly")
    start_date_entry.pack(side="left", padx=10, pady=10)

    # Create a label and a DateEntry widget for the end date
    end_date_label = tk.Label(top_frame, text="End Date:")
    end_date_label.pack(side="left", padx=10, pady=10)
    end_date_entry = DateEntry(top_frame, date_pattern="yyyy-mm-dd", state="readonly")
    end_date_entry.pack(side="left", padx=10, pady=10)

    # Create a combobox for the status selection
    status_combobox = ttk.Combobox(status_frame, state="readonly", values=["", "Registered", "Not Registered"])
    status_combobox.pack(side="left", padx=10, pady=10)

    # Create a button to retrieve the data
    retrieve_button = tk.Button(top_frame, text="Retrieve Data", command=retrieve_data)
    retrieve_button.pack(side="left", padx=10, pady=10)

    # Create a button to export the retrieved data
    export_button = tk.Button(top_frame, text="Export", command=export_retrieved_data, state="disabled")
    export_button.pack(side="left", padx=10, pady=10)

    # Create a Treeview to display the result
    result_tree = ttk.Treeview(advanced_window, columns=("Entering Time", "Exit Time", "Car Plate", "Status"),
                               show="headings")
    result_tree.pack(fill='both', expand=True)

    # Set the column headings
    result_tree.heading("Entering Time", text="Entering Time")
    result_tree.heading("Exit Time", text="Exit Time")
    result_tree.heading("Car Plate", text="Car Plate")
    result_tree.heading("Status", text="Status")

    # Set the column widths
    result_tree.column("Entering Time", width=150)
    result_tree.column("Exit Time", width=150)
    result_tree.column("Car Plate", width=150)
    result_tree.column("Status", width=150)

    # Center the advanced_window on the screen
    center_window(advanced_window)


# Define a second side window to create advanced window
def create_second_advanced_window():
    global second_advanced_window, car_plate_entry, car_plate_status_combo, result_tree, export_button_car

    # Check if the second_advanced_window already exists
    close_side_window()  # Destroy the existing second_advanced_window

    # Create a new Toplevel window
    second_advanced_window = tk.Toplevel(window)
    second_advanced_window.geometry("800x450")
    second_advanced_window.title("Advanced Search (Car Plate)")

    # Set the second_advanced_window as a transient window of the main window
    second_advanced_window.transient(window)

    # Override the default close window behavior
    second_advanced_window.protocol("WM_DELETE_WINDOW", confirm_exit)

    # Create a frame for the entry box and combobox
    top_frame = tk.Frame(second_advanced_window)
    top_frame.pack(side="top", padx=10, pady=10)

    # Create a frame for the Treeview
    tree_frame = tk.Frame(second_advanced_window)
    tree_frame.pack(side="top", fill='both', expand=True, padx=10, pady=10)

    # Create a label and an entry box for the car plate starting character
    car_plate_label = tk.Label(top_frame, text="Car Plate Starting Character:")
    car_plate_label.pack(side="left", padx=10, pady=10)
    car_plate_entry = tk.Entry(top_frame)
    car_plate_entry.pack(side="left", padx=10, pady=10)

    # Create a ComboBox to select car plate status
    car_plate_status_label = tk.Label(top_frame, text="Car Plate Status:")
    car_plate_status_label.pack(side="left", padx=10, pady=10)
    car_plate_status_combo = ttk.Combobox(top_frame, values=["", "Expired", "Valid"], state="readonly")
    car_plate_status_combo.pack(side="left", padx=10, pady=10)

    # Create a button to retrieve data
    retrieve_button = tk.Button(top_frame, text="Retrieve Data", command=search_advanced_car_plate)
    retrieve_button.pack(side="left", padx=10, pady=10)

    # Create a button to export the retrieved data
    export_button_car = tk.Button(top_frame, text="Export", command=export_retrieved_car_plate, state="disabled")
    export_button_car.pack(side="left", padx=10, pady=10)

    # Create a Treeview to display the search results
    result_tree = ttk.Treeview(tree_frame, columns=("Serial Number", "Car Plate", "Valid Date", "ID"),
                               show="headings")
    result_tree.pack(fill='both', expand=True)

    # Set the column headings
    result_tree.heading("Serial Number", text="Serial Number")
    result_tree.heading("Car Plate", text="Car Plate")
    result_tree.heading("Valid Date", text="Valid Date")
    result_tree.heading("ID", text="ID")

    # Set the column widths
    result_tree.column("Serial Number", width=150)
    result_tree.column("Car Plate", width=150)
    result_tree.column("Valid Date", width=150)
    result_tree.column("ID", width=150)

    # Center the second_advanced_window on the screen
    center_window(second_advanced_window)


# Define a function for advanced search car plates
def search_advanced_car_plate():
    starting_character = car_plate_entry.get().upper()
    status = car_plate_status_combo.get()

    # Read the car plate data from the CSV file
    with open("Car_plates.csv", "r") as csv_file:
        reader = csv.DictReader(csv_file)
        car_plate_data = list(reader)

    # Filter the car plate data based on the starting character
    filtered_data = [
        row
        for row in car_plate_data
        if row["Car Plate"].startswith(starting_character)
    ]

    # Calculate the status based on the "Valid Until" date
    current_date = datetime.date.today()
    if status == "Valid":
        filtered_data = [
            row
            for row in filtered_data
            if datetime.datetime.strptime(row["Valid Until"], "%Y-%m-%d").date() >= current_date
        ]
    elif status == "Expired":
        filtered_data = [
            row
            for row in filtered_data
            if datetime.datetime.strptime(row["Valid Until"], "%Y-%m-%d").date() < current_date
        ]

    # Clear any existing data in the Treeview
    result_tree.delete(*result_tree.get_children())

    # Insert the filtered data into the Treeview
    for row in filtered_data:
        result_tree.insert("", "end", values=(row["Serial Number"], row["Car Plate"], row["Valid Until"], row["ID"]))

    # Enable or disable the export button based on the retrieved data
    if len(filtered_data) > 0:
        export_button_car.config(state="normal")
    else:
        export_button_car.config(state="disabled")


# Function to center the side window
def center_window(window):
    # Update the window to ensure it's fully rendered
    window.update()

    # Get the window dimensions
    window_width = window.winfo_width()
    window_height = window.winfo_height()

    # Calculate the position coordinates
    position_top = int(window.winfo_screenheight() / 2 - window_height / 2)
    position_left = int(window.winfo_screenwidth() / 2 - window_width / 2)

    # Set the window position
    window.geometry("+{}+{}".format(position_left, position_top))


# Function to close the side window
def close_side_window():
    # Check if the add_window exists
    if 'add_window' in globals() and add_window is not None:
        add_window.destroy()  # Destroy the existing add_window

    # Check if the search_window exists
    if 'search_window' in globals() and search_window is not None:
        search_window.destroy()  # Destroy the existing search_window

    # Check if the advanced_window exists
    if 'advanced_window' in globals() and advanced_window is not None:
        advanced_window.destroy()  # Destroy the existing advanced_window

    # Check if the second_advanced_window exists
    if 'second_advanced_window' in globals() and second_advanced_window is not None:
        second_advanced_window.destroy()  # Destroy the existing advanced_window


# Define function to confirm exit
def confirm_exit():
    if messagebox.askokcancel("Quit", "Do you really wish to quit?"):
        close_side_window()


def confirm_exit_main():
    answer = messagebox.askyesno("Exit Confirmation", "Are you sure you want to exit?")
    if answer:
        window.destroy()


# Define function to retrieve data for Advanced window
def retrieve_data():
    start_date = start_date_entry.get_date()
    end_date = end_date_entry.get_date()
    status = status_combobox.get()

    # Check if the start and end dates are provided
    if not start_date or not end_date:
        messagebox.showerror("Error", "Please provide both start and end dates.")
        return

    # Check if the end date is earlier than the start date
    if end_date < start_date:
        messagebox.showerror("Error", "End date cannot be earlier than the start date.")
        return

    # Read the Realtime_results.csv file
    with open("Realtime_results.csv", "r") as csv_file:
        reader = csv.DictReader(csv_file)
        data = list(reader)

    # Filter the data based on the selected date range and status
    filtered_data = [
        row
        for row in data
        if start_date <= datetime.datetime.strptime(row["Entering Time"], "%Y-%m-%d %H:%M:%S").date() <= end_date
           and (status == "" or (status == "Registered" and row["Registered"].lower() == "yes") or (
                status == "Not Registered" and row["Registered"].lower() == "no"))
    ]

    # Clear any existing data in the Treeview
    result_tree.delete(*result_tree.get_children())

    # Insert the filtered data into the Treeview
    for row in filtered_data:
        result_tree.insert("", "end",
                           values=(row["Entering Time"], row["Exit Time"], row["Car Plate"], row["Registered"]))

    # Enable or disable the export button based on the retrieved data
    if len(filtered_data) > 0:
        export_button.config(state="normal")
    else:
        export_button.config(state="disabled")


# Define a function to export retrieved data
def export_retrieved_data():
    # Check if there is data in the Treeview
    if len(result_tree.get_children()) == 0:
        messagebox.showwarning("No Data", "There is no data to export.")
        return

    # Prompt the user to select a save location
    save_location = filedialog.asksaveasfilename(
        initialfile="RetrievedCarEntryData.csv",
        defaultextension=".csv",
        filetypes=[("CSV Files", "*.csv")]
    )

    # Check if the user selected a save location
    if not save_location:
        return

    # Retrieve the data from the Treeview
    data = []
    for item in result_tree.get_children():
        values = result_tree.item(item, "values")
        data.append(values)

    # Write the data to the CSV file
    with open(save_location, "w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["Entering Time", "Exit Time", "Car Plate", "Status"])
        writer.writerows(data)

    messagebox.showinfo("Export Successful", "The retrieved data has been exported successfully.")


# Define a function to export retrieved car plate data
def export_retrieved_car_plate():
    # Check if there is data in the Treeview
    if len(result_tree.get_children()) == 0:
        messagebox.showwarning("No Data", "There is no data to export.")
        return

    # Prompt the user to select a save location
    save_location = filedialog.asksaveasfilename(
        initialfile="RetrievedCarPlateData.csv",
        defaultextension=".csv",
        filetypes=[("CSV Files", "*.csv")]
    )

    # Check if the user selected a save location
    if not save_location:
        return

    # Retrieve the data from the Treeview
    data = []
    for item in result_tree.get_children():
        values = result_tree.item(item, "values")
        data.append(values)

    # Write the data to the CSV file
    with open(save_location, "w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["Serial Number", "Car Plate", "Valid Date", "ID"])
        writer.writerows(data)

    messagebox.showinfo("Export Successful", "The retrieved car plate data has been exported successfully.")


# Function to create the menu bar
def create_menu_bar():
    # Create a menu bar
    menu_bar = tk.Menu(window)
    window.config(menu=menu_bar)

    # Create the File menu
    file_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="File", menu=file_menu)

    # Create a submenu for exporting options
    export_menu = tk.Menu(file_menu, tearoff=0)
    file_menu.add_cascade(label="Export CSV", menu=export_menu)

    # Add the export options to the submenu
    export_menu.add_command(label="Export Car Entry(All)", command=lambda: export_csv("Car Entry List"))
    export_menu.add_command(label="Export Registered Cars(All)", command=lambda: export_csv("Registered Cars"))

    # Add a separator in the file menu
    file_menu.add_separator()

    # Add the Export Plot Diagram option
    file_menu.add_command(label="Export Plot Diagram", command=export_plot_diagram)

    # Add a separator in the file menu
    file_menu.add_separator()

    # Add the Open Realtime Images Folder option
    file_menu.add_command(label="Open Detected Images Folder", command=open_realtime_images_folder)
    file_menu.add_command(label="Exit", command=confirm_exit_main)

    # Create the Car Plate menu
    car_plate_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Management", menu=car_plate_menu)
    car_plate_menu.add_command(label="Activate", command=run_exe)
    car_plate_menu.add_command(label="Capture Face", command=capture_faces)
    car_plate_menu.add_command(label="Add Car Plate", command=create_add_window)
    car_plate_menu.add_command(label="Search Car Plate", command=create_search_window)

    # Create the Advanced Search menu
    advanced_search_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Advanced Search", menu=advanced_search_menu)
    advanced_search_menu.add_command(label="Advanced Search (Car Entry)", command=create_advanced_window)
    advanced_search_menu.add_command(label="Advanced Search (Car Plate)", command=create_second_advanced_window)


# Function to capture faces
def capture_faces():
    # Load the pre-trained face detection classifier
    face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

    # Open the camera
    cap = cv2.VideoCapture(0)

    # Create the "Captured Faces" directory if it doesn't exist
    if not os.path.exists('Captured Faces'):
        os.makedirs('Captured Faces')

    def get_last_face_count():
        # Get the list of existing face images in the folder
        files = os.listdir('Captured Faces')

        # Filter and extract the face count numbers
        face_counts = [int(file.split('_')[1].split('.')[0]) for file in files if file.startswith('face_')]

        if len(face_counts) > 0:
            # Get the maximum face count
            last_face_count = max(face_counts)
        else:
            last_face_count = 0

        return last_face_count

    capturing = False  # Flag to indicate whether capturing is in progress
    face_count = get_last_face_count() + 1  # Start face count from the last saved face + 1

    while True:
        # Read the current frame from the camera
        ret, frame = cap.read()

        # Convert the frame to grayscale for face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect faces in the grayscale frame
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        # Draw rectangles around the detected faces
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # Display the frame
        cv2.imshow('Face Detection', frame)

        # Check for key press
        key = cv2.waitKey(1)

        # Press 'c' to start capturing faces
        if key & 0xFF == ord('c') and not capturing:
            if len(faces) > 0:
                capturing = True
                for (x, y, w, h) in faces:
                    face_img = frame[y:y + h, x:x + w]
                    cv2.imwrite(f'Captured Faces/face_{face_count}.jpg', face_img)
                    print(f"Captured face_{face_count}.jpg")
                    face_count += 1
                messagebox.showinfo("Capture Successful", "Face captured successfully.")
                capturing = False  # reset capturing to False after you've captured the face(s)
            else:
                messagebox.showwarning("No Face Detected", "No faces detected to capture.")

        # Press 'q' to exit the program
        elif key & 0xFF == ord('q'):
            confirm = messagebox.askyesno("Exit Confirmation",
                                          "Are you sure you want to exit?\nPress 'Yes' to confirm or 'No' to continue.")
            if confirm:
                break

    # Release the camera and close all windows
    cap.release()
    cv2.destroyAllWindows()


# Function to read the last 30 rows of the CSV file
def read_csv():
    csv_file = 'Realtime_results.csv'
    if not os.path.exists(csv_file):
        # Create the CSV file with the appropriate headers
        with open(csv_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Entering Time", "Exit Time", "Car Plate", "Registered"])
            # Return an empty DataFrame with the appropriate columns
        return pd.DataFrame(columns=["Entering Time", "Exit Time", "Car Plate", "Registered"])
    df = pd.read_csv(csv_file)
    return df.tail(30)


# Function to display the data in the Treeview
def display_data(tree):
    # Delete old rows
    for i in tree.get_children():
        tree.delete(i)

    # Read the CSV data
    df = read_csv()

    # Add new rows
    registered_count = df[df['Registered'] == 'Yes'].shape[0]
    not_registered_count = df[df['Registered'] == 'No'].shape[0]

    # Insert the filtered data into the Treeview
    for index, row in df.iterrows():
        tree.insert("", "end", values=list(row))

    # Update the main window label with the counts
    registered_label.config(text=f"Registered: {registered_count}")
    not_registered_label.config(text=f"Not Registered: {not_registered_count}")


# Function to sort the data
def sortby(tree, col, descending):
    """Function to sort tree contents when a column is clicked on."""
    # Grab values to sort
    data = [(tree.set(child, col), child) for child in tree.get_children('')]

    # Sort the data
    data.sort(reverse=descending)

    # Rearrange items in sorted positions
    for ix, item in enumerate(data):
        tree.move(item[1], '', ix)

    # Switch the heading so that it will sort in the opposite direction
    tree.heading(col, command=lambda col=col: sortby(tree, col, int(not descending)))

    # Change the column heading to include an arrow
    if descending:
        tree.heading(col, text=f"{col} ↓")
    else:
        tree.heading(col, text=f"{col} ↑")


# Function to refresh the CSV data
def refresh_data(tree):
    display_data(tree)


def open_realtime_images_folder():
    try:
        # Get the path to the "Realtime_Images" folder
        folder_path = os.path.join(os.getcwd(), "Realtime_Images")

        # Open the "Realtime_Images" folder in the default file explorer
        os.startfile(folder_path)
    except Exception as e:
        messagebox.showerror('Error', f'Failed to open the "Realtime_Images" folder: {str(e)}')


# Function to export csv file
def export_csv(file_name):
    source_file = 'Realtime_results.csv' if file_name == "Car Entry List" else 'Car_plates.csv'

    # Check if the source file exists
    if not os.path.exists(source_file):
        messagebox.showerror("Error", f"The '{source_file}' file does not exist.")
        return

    # Prompt the user to select a save location with the chosen file name
    save_location = filedialog.asksaveasfilename(
        initialfile=file_name + ".csv",
        defaultextension=".csv",
        filetypes=[("CSV Files", "*.csv")]
    )

    # Check if the user selected a save location
    if not save_location:
        return

    # Copy the source file to the save location
    try:
        shutil.copyfile(source_file, save_location)
        messagebox.showinfo("Success", f"The file has been exported as '{file_name}'.")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while exporting the file: {str(e)}")


# Update time in the main window
def update_time():
    current_date_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    date_time_label.config(text=current_date_time)
    date_time_label.after(1000, update_time)  # Update every 1000 milliseconds (1 second)


# Function to plot the data
def plot_data():
    # If a canvas already exists, destroy it
    if hasattr(window, 'canvas'):
        window.canvas.get_tk_widget().destroy()

    # Read the CSV data
    df = pd.read_csv('Realtime_results.csv')

    # Convert the 'Entering Time' and 'Exit Time' columns to datetime
    df['Entering Time'] = pd.to_datetime(df['Entering Time'])
    df['Exit Time'] = pd.to_datetime(df['Exit Time'])

    # Extract the hour from the datetime
    df['Entering Hour'] = df['Entering Time'].dt.hour
    df['Exit Hour'] = df['Exit Time'].dt.hour

    # Count the number of entries/exits for each hour
    entry_counts = df['Entering Hour'].value_counts().sort_index()
    exit_counts = df['Exit Hour'].value_counts().sort_index()

    # Create a Figure
    fig = Figure(figsize=(6, 4), dpi=100)
    ax = fig.add_subplot(111)

    # Set the data for the histogram
    entries = ax.bar(entry_counts.index, entry_counts.values, alpha=0.7, label='Entries')
    exits = ax.bar(exit_counts.index, exit_counts.values, alpha=0.7, label='Exits')

    # Set the x-axis labels to 12-hour format
    ax.set_xticks(range(24))
    ax.set_xticklabels([f'{i % 12 or 12} {"AM" if i < 12 else "PM"}' for i in range(24)])

    ax.set_xlabel('Hour of the Day')
    ax.set_ylabel('Number of Cars')
    ax.set_title('Number of Car Entries and Exits by Hour')
    ax.legend()

    # Create a canvas and draw the plot on it
    canvas = FigureCanvasTkAgg(fig, master=window)
    canvas.draw()
    canvas.get_tk_widget().pack(side="top", fill='both', expand=True)

    # Add cursor to show hover data
    cursor = mplcursors.cursor(ax, hover=True)
    cursor.connect(
        "add",
        lambda sel: sel.annotation.set_text(
            f"Hour: {int(round(sel.target[0])) % 12 or 12} {'AM' if int(round(sel.target[0])) < 12 else 'PM'}, Count: {int(sel.target[1])}"
        )
    )

    # Store the canvas as an attribute of the window
    window.canvas = canvas


# Function to export the plot diagram
def export_plot_diagram():
    # If a canvas exists, save the plot to a PDF file
    if hasattr(window, 'canvas'):
        fig = window.canvas.figure

        # Get the current date
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")

        # Prompt the user to select a save location for the PDF file
        save_location = filedialog.asksaveasfilename(
            initialfile=f"Car Entries and Exits by Hour_{current_date}.pdf",
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")]
        )

        # Check if the user selected a save location
        if not save_location:
            return

        try:
            # Save the plot to the selected location as a PDF file
            fig.savefig(save_location)
            messagebox.showinfo('Export', f'Plot diagram exported to {save_location}.')
        except Exception as e:
            messagebox.showerror('Export Error', f'An error occurred while exporting the plot diagram: {str(e)}')
    else:
        messagebox.showwarning('Export', 'No plot diagram to export.')


# Create the GUI window
window = tk.Tk()
window.geometry("1300x800")
window.title("Car Plate System Manager")

# Calculate the screen width and height
screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()

# Calculate the x and y positions for centering the window
x = (screen_width // 2) - (1300 // 2)  # Adjust the width of the window if needed
y = (screen_height // 2) - (800 // 2)  # Adjust the height of the window if needed

# Set the window geometry
window.geometry(f"1300x800+{x}+{y}")

# Create the menu bar
create_menu_bar()

# Create a label for the current date/time
date_time_label = tk.Label(window, text="", font=("Arial", 12, "bold"))
date_time_label.pack(side="top", padx=10, pady=10)

# Start updating the time label
update_time()

# Create a frame for the top left corner
top_left_frame = tk.Frame(window)
top_left_frame.pack(anchor="nw", padx=10, pady=10)

# Create a label for "Car Entry"
car_entry_label = tk.Label(top_left_frame, text="Car Entry(Recent 30 Entries)", font=("Arial", 14, "bold"))
car_entry_label.pack(side="left")

# Create the 'Refresh' button
refresh_button = tk.Button(top_left_frame, text="Refresh", command=lambda: refresh_data(tree))
refresh_button.pack(side="left", padx=(10, 0))

# Create the 'Plot' button
plot_button = tk.Button(top_left_frame, text="Plot", command=plot_data)
plot_button.pack(side="left", padx=(10, 0))

# Create a label for the registered count
registered_label = tk.Label(top_left_frame, text="Registered: 0")
registered_label.pack(side="left", padx=(10, 0))

# Create a label for the not registered count
not_registered_label = tk.Label(top_left_frame, text="Not Registered: 0")
not_registered_label.pack(side="left", padx=(10, 0))

# Create a frame for the Treeview and Scrollbar
tree_frame = tk.Frame(window)
tree_frame.pack(fill='both', expand=True)

# Create a Scrollbar
scrollbar = ttk.Scrollbar(tree_frame)
scrollbar.pack(side='right', fill='y')

# Create a Treeview
tree = ttk.Treeview(tree_frame, columns=("Entering Time", "Exit Time", "Car Plate"), show="headings",
                    yscrollcommand=scrollbar.set)

# Configure Scrollbar to move the Treeview
scrollbar.config(command=tree.yview)

# Call sortby function for each column header
for col in ("Entering Time", "Exit Time", "Car Plate"):
    tree.heading(col, text=col, command=lambda _col=col: sortby(tree, _col, False))

tree.pack(fill='both', expand=True)

# Display the initial data
display_data(tree)

# Start the GUI loop
window.protocol("WM_DELETE_WINDOW", confirm_exit_main)
window.mainloop()
