import fitz  # PyMuPDF
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk

class PDFTextExtractorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Text Extractor")

        # Left side: Canvas for PDF display
        self.canvas = tk.Canvas(self.root)
        self.canvas.pack(expand=True, fill="both", side="left")

        # Right side: Frame for buttons and search results
        self.right_frame = tk.Frame(self.root)
        self.right_frame.pack(expand=True, fill="both", side="right")

        # Buttons
        self.load_button = tk.Button(self.right_frame, text="Load PDF", command=self.load_pdf)
        self.load_button.grid(row=0, column=0, padx=5, pady=5)

        self.extract_button = tk.Button(self.right_frame, text="Extract Text", command=self.extract_text)
        self.extract_button.grid(row=0, column=1, padx=5, pady=5)

        self.prev_page_button = tk.Button(self.right_frame, text="Previous Page", command=self.prev_page)
        self.prev_page_button.grid(row=0, column=2, padx=5, pady=5)

        self.next_page_button = tk.Button(self.right_frame, text="Next Page", command=self.next_page)
        self.next_page_button.grid(row=0, column=3, padx=5, pady=5)

        self.back_button = tk.Button(self.right_frame, text="Back", command=self.clear_search)
        self.back_button.grid(row=1, column=3, padx=5, pady=5)

        # Page navigation
        self.page_label = tk.Label(self.right_frame, text="Go to Page:")
        self.page_label.grid(row=2, column=0, padx=5, pady=5)

        self.page_entry = tk.Entry(self.right_frame)
        self.page_entry.grid(row=2, column=1, padx=5, pady=5)

        self.go_to_page_button = tk.Button(self.right_frame, text="Go", command=self.go_to_page)
        self.go_to_page_button.grid(row=2, column=2, padx=5, pady=5)

        # Search
        self.search_label = tk.Label(self.right_frame, text="Search:")
        self.search_label.grid(row=1, column=0, padx=5, pady=5)

        self.search_entry = tk.Entry(self.right_frame)
        self.search_entry.grid(row=1, column=1, padx=5, pady=5)

        self.search_button = tk.Button(self.right_frame, text="Search", command=self.search_text)
        self.search_button.grid(row=1, column=2, padx=5, pady=5)

        # Text area for search results
        self.result_text = scrolledtext.ScrolledText(self.right_frame, wrap=tk.WORD, width=50)
        self.result_text.grid(row=3, column=0, columnspan=4, padx=5, pady=5, sticky="nsew")
        self.right_frame.grid_rowconfigure(3, weight=1)  # Make row 3 expandable
        self.right_frame.grid_columnconfigure(0, weight=1)  # Make column 0 expandable


        # PDF document and current page number
        self.pdf_doc = None
        self.current_page_num = tk.IntVar(value=0)

    def clear_search(self):
        self.result_text.delete(1.0, tk.END)
        self.display_extracted_text(self.text_in_area)

    def go_to_page(self):
        page_num = int(self.page_entry.get())
        if 1 <= page_num <= len(self.pdf_doc):
            self.current_page_num.set(page_num - 1)
            self.display_current_page()
        else:
            messagebox.showerror("Error", f"Invalid page number. Please enter a page number between 1 and {len(self.pdf_doc)}.")


    def load_pdf(self):
        self.current_page_num.set(0)
        pdf_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if pdf_path:
            self.pdf_doc = fitz.open(pdf_path)
            self.display_current_page()

    def display_current_page(self):
        if self.pdf_doc:
            self.canvas.delete("all")
            page = self.pdf_doc.load_page(self.current_page_num.get())
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img = ImageTk.PhotoImage(img)
            self.canvas.config(width=pix.width, height=pix.height)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=img)
            self.canvas.image = img

    def prev_page(self):
        if self.pdf_doc and self.current_page_num.get() > 0:
            self.current_page_num.set(self.current_page_num.get() - 1)
            self.display_current_page()

    def next_page(self):
        if self.pdf_doc and self.current_page_num.get() < len(self.pdf_doc) - 1:
            self.current_page_num.set(self.current_page_num.get() + 1)
            self.display_current_page()

    def extract_text(self):
        if not self.pdf_doc:
            messagebox.showerror("Error", "Please load a PDF file first.")
            return

        x0, y0, x1, y1 = self.get_rectangle_coords()
        if x0 == x1 or y0 == y1:
            messagebox.showerror("Error", "Please draw a rectangle on the PDF.")
            return

        self.text_in_area = {}  # Initialize text_in_area dictionary
        for page_number in range(len(self.pdf_doc)):
            page = self.pdf_doc.load_page(page_number)
            text = page.get_text("text", clip=(x0, y0, x1, y1))
            self.text_in_area[page_number + 1] = text.strip()  # Store extracted text for the page

        self.display_extracted_text(self.text_in_area)  # Display extracted text in the result_text widget


    def display_extracted_text(self, text_in_area):
        self.result_text.delete(1.0, tk.END)
        for page, text in text_in_area.items():
            self.result_text.insert(tk.END, f"Page {page}:\n{text}\n\n")

    def search_text(self):
        search_text = self.search_entry.get().lower()
        if search_text:
            self.result_text.delete(1.0, tk.END)
            self.filtered_text_in_area = {}
            for page_number, text in self.text_in_area.items():
                if search_text in text.lower():
                    self.filtered_text_in_area[page_number] = text.strip()
                    self.result_text.insert(tk.END, f"Page {page_number}:\n{text.strip()}\n\n")
            self.highlight_search_results(search_text)


    def highlight_search_results(self, search_text):
        self.result_text.tag_remove("found", "1.0", tk.END)
        start = "1.0"
        while True:
            start = self.result_text.search(search_text, start, tk.END, nocase=True)
            if not start:
                break
            end = f"{start}+{len(search_text)}c"
            self.result_text.tag_add("found", start, end)
            start = end
        self.result_text.tag_config("found", background="yellow")
        self.result_text.focus_set()


    def get_rectangle_coords(self):
        try:
            x0, y0, x1, y1 = self.canvas.coords(self.rect)
            return int(x0), int(y0), int(x1), int(y1)
        except AttributeError:
            return 0, 0, 0, 0

    def on_left_click(self, event):
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='blue')

    def on_drag(self, event):
        cur_x = self.canvas.canvasx(event.x)
        cur_y = self.canvas.canvasy(event.y)
        self.canvas.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)

if __name__ == "__main__":
    root = tk.Tk()
    app = PDFTextExtractorApp(root)
    app.canvas.bind("<Button-1>", app.on_left_click)
    app.canvas.bind("<B1-Motion>", app.on_drag)
    root.mainloop()
