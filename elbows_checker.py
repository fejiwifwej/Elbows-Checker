import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import cv2
import numpy as np
from PIL import Image, ImageTk
import os

class ElbowsChecker:
    def __init__(self, root):
        self.root = root
        self.root.title("Elbows Checker - The Ultimate Beer Cap Justice Tool")
        self.root.geometry("1200x800")
        
        # Variables
        self.original_image = None
        self.processed_image = None
        self.image_tk = None
        self.points = []
        self.line_start = None
        self.line_end = None
        self.drawing_line = False
        
        # Scaling and positioning variables
        self.current_scale = 1.0
        self.display_offset_x = 0
        self.display_offset_y = 0
        
        # Mode variables
        self.current_mode = "corners"  # "corners" or "line"
        
        # Create GUI
        self.create_widgets()
        
    def create_widgets(self):
        # Main frame
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel for controls
        left_panel = tk.Frame(main_frame, width=300)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # Title
        title_label = tk.Label(left_panel, text="🍺 Elbows Checker 🍺", 
                             font=("Arial", 16, "bold"), fg="red")
        title_label.pack(pady=10)
        
        subtitle = tk.Label(left_panel, text="Settling Beer Cap Disputes Since 2024", 
                           font=("Arial", 10), fg="gray")
        subtitle.pack(pady=(0, 20))
        
        # File operations
        file_frame = tk.LabelFrame(left_panel, text="📁 File Operations", padx=10, pady=10)
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Button(file_frame, text="Load Image", command=self.load_image, 
                 bg="lightblue", font=("Arial", 10, "bold")).pack(fill=tk.X, pady=5)
        
        tk.Button(file_frame, text="Save Image", command=self.save_image, 
                 bg="lightgreen", font=("Arial", 10, "bold")).pack(fill=tk.X, pady=5)
        
        # Mode selection
        mode_frame = tk.LabelFrame(left_panel, text="🔄 Mode Selection", padx=10, pady=10)
        mode_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.mode_button = tk.Button(mode_frame, text="Switch to Line Drawing Mode", 
                                    command=self.toggle_mode, 
                                    bg="lightblue", font=("Arial", 10, "bold"))
        self.mode_button.pack(fill=tk.X, pady=5)
        
        self.mode_label = tk.Label(mode_frame, text="Current Mode: Select Corners", 
                                  font=("Arial", 10, "bold"), fg="blue")
        self.mode_label.pack(pady=5)
        
        # Perspective correction
        self.perspective_frame = tk.LabelFrame(left_panel, text="🔧 Perspective Correction", padx=10, pady=10)
        self.perspective_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(self.perspective_frame, text="Click 4 points to define the table surface:").pack()
        tk.Label(self.perspective_frame, text="Select any rectangular area on the table", fg="blue").pack()
        tk.Label(self.perspective_frame, text="1. Top-left corner of the area", fg="blue").pack()
        tk.Label(self.perspective_frame, text="2. Top-right corner of the area", fg="blue").pack()
        tk.Label(self.perspective_frame, text="3. Bottom-right corner of the area", fg="blue").pack()
        tk.Label(self.perspective_frame, text="4. Bottom-left corner of the area", fg="blue").pack()
        tk.Label(self.perspective_frame, text="(The entire image will be warped)", fg="gray", font=("Arial", 8)).pack()
        
        tk.Button(self.perspective_frame, text="Apply Perspective Correction", 
                 command=self.apply_perspective, bg="orange", font=("Arial", 10, "bold")).pack(fill=tk.X, pady=10)
        
        tk.Button(self.perspective_frame, text="Reset Points", 
                 command=self.reset_points, bg="lightcoral").pack(fill=tk.X, pady=5)
        
        # Line drawing
        self.line_frame = tk.LabelFrame(left_panel, text="📏 Draw Elbow Line", padx=10, pady=10)
        self.line_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(self.line_frame, text="Click and drag to draw a red line:").pack()
        tk.Label(self.line_frame, text="This will be your 'elbow line' evidence", fg="red").pack()
        
        tk.Button(self.line_frame, text="Clear Line", 
                 command=self.clear_line, bg="lightcoral").pack(fill=tk.X, pady=5)
        
        # Initially hide line frame since we start in corners mode
        self.update_mode_visibility()
        
        # Status
        self.status_label = tk.Label(left_panel, text="Ready to settle disputes! Select corners mode active.", 
                                   font=("Arial", 10), fg="green")
        self.status_label.pack(pady=20)
        
        # Right panel for image display
        right_panel = tk.Frame(main_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Canvas for image display
        self.canvas = tk.Canvas(right_panel, bg="white", cursor="cross")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Bind mouse events
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        
    def toggle_mode(self):
        if self.current_mode == "corners":
            self.current_mode = "line"
            self.mode_button.config(text="Switch to Corner Selection Mode", bg="lightcoral")
            self.mode_label.config(text="Current Mode: Draw Line", fg="red")
            self.canvas.config(cursor="crosshair")
            self.status_label.config(text="Line drawing mode active. Click and drag to draw elbow line.")
        else:
            self.current_mode = "corners"
            self.mode_button.config(text="Switch to Line Drawing Mode", bg="lightblue")
            self.mode_label.config(text="Current Mode: Select Corners", fg="blue")
            self.canvas.config(cursor="cross")
            self.status_label.config(text="Corner selection mode active. Click to select 4 corners.")
        
        self.update_mode_visibility()
        # Only redraw if we have valid scaling info
        if hasattr(self, 'current_scale') and self.processed_image is not None:
            self.display_image()
        
    def update_mode_visibility(self):
        if self.current_mode == "corners":
            self.perspective_frame.pack(fill=tk.X, pady=(0, 10))
            self.line_frame.pack_forget()
        else:
            self.line_frame.pack(fill=tk.X, pady=(0, 10))
            self.perspective_frame.pack_forget()
    
    def load_image(self):
        file_path = filedialog.askopenfilename(
            title="Select the incriminating photo",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff")]
        )
        
        if file_path:
            try:
                self.original_image = cv2.imread(file_path)
                self.processed_image = self.original_image.copy()
                self.display_image()
                self.points = []
                self.line_start = None
                self.line_end = None
                self.status_label.config(text=f"Loaded: {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load image: {str(e)}")
    
    def display_image(self):
        if self.processed_image is None:
            return
            
        # Convert BGR to RGB
        image_rgb = cv2.cvtColor(self.processed_image, cv2.COLOR_BGR2RGB)
        
        # Force canvas to update its dimensions
        self.canvas.update_idletasks()
        
        # Resize to fit canvas
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # Ensure we have valid canvas dimensions
        if canvas_width <= 1 or canvas_height <= 1:
            self.root.after(10, self.display_image)  # Retry after a short delay
            return
        # Calculate scaling
        img_height, img_width = image_rgb.shape[:2]
        scale_x = canvas_width / img_width
        scale_y = canvas_height / img_height
        scale = min(scale_x, scale_y)
        
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        # Store scaling info for coordinate conversion
        self.current_scale = scale
        self.display_offset_x = canvas_width // 2 - new_width // 2
        self.display_offset_y = canvas_height // 2 - new_height // 2
        
        # Resize image
        image_resized = cv2.resize(image_rgb, (new_width, new_height))
        
        # Convert to PhotoImage
        image_pil = Image.fromarray(image_resized)
        self.image_tk = ImageTk.PhotoImage(image_pil)
        
        # Clear canvas and display image
        self.canvas.delete("all")
        self.canvas.create_image(
            canvas_width // 2, canvas_height // 2,
            image=self.image_tk, anchor=tk.CENTER
        )
        
        # Draw points (only in corners mode)
        if self.current_mode == "corners":
            for i, point in enumerate(self.points):
                x, y = point
                scaled_x = int(x * scale) + self.display_offset_x
                scaled_y = int(y * scale) + self.display_offset_y
                
                color = "red" if i < len(self.points) - 1 else "green"
                self.canvas.create_oval(scaled_x-5, scaled_y-5, scaled_x+5, scaled_y+5, 
                                     fill=color, outline="white", tags="point")
                self.canvas.create_text(scaled_x, scaled_y-15, text=str(i+1), 
                                     fill="white", font=("Arial", 12, "bold"), tags="point")
        
        # Draw line (only in line mode or when line exists)
        if self.line_start and self.line_end:
            start_x, start_y = self.line_start
            end_x, end_y = self.line_end
            
            scaled_start_x = int(start_x * scale) + self.display_offset_x
            scaled_start_y = int(start_y * scale) + self.display_offset_y
            scaled_end_x = int(end_x * scale) + self.display_offset_x
            scaled_end_y = int(end_y * scale) + self.display_offset_y
            
            self.canvas.create_line(scaled_start_x, scaled_start_y, scaled_end_x, scaled_end_y,
                                 fill="red", width=3, tags="line")
    
    def canvas_to_image_coords(self, canvas_x, canvas_y):
        """Convert canvas coordinates to image coordinates using stored scaling info"""
        if not hasattr(self, 'current_scale') or not hasattr(self, 'display_offset_x'):
            return None, None
            
        img_x = (canvas_x - self.display_offset_x) / self.current_scale
        img_y = (canvas_y - self.display_offset_y) / self.current_scale
        
        # Check if coordinates are within image bounds
        if self.processed_image is not None:
            img_height, img_width = self.processed_image.shape[:2]
            if 0 <= img_x <= img_width and 0 <= img_y <= img_height:
                return img_x, img_y
        
        return None, None
    
    def on_canvas_click(self, event):
        if self.processed_image is None:
            return
            
        # Convert canvas coordinates to image coordinates using stored scaling
        img_x, img_y = self.canvas_to_image_coords(event.x, event.y)
        
        if img_x is None or img_y is None:
            return  # Click was outside image bounds
            
        if self.current_mode == "corners" and len(self.points) < 4:
            self.points.append((img_x, img_y))
            self.status_label.config(text=f"Point {len(self.points)} added. {4-len(self.points)} more needed.")
            self.display_image()
        elif self.current_mode == "line":
            # Start drawing line
            self.line_start = (img_x, img_y)
            self.drawing_line = True
            self.status_label.config(text="Drag to draw the elbow line...")
        elif self.current_mode == "corners" and len(self.points) >= 4:
            self.status_label.config(text="4 points already selected. Apply correction or reset points.")
    
    def on_canvas_drag(self, event):
        if self.current_mode == "line" and self.drawing_line and self.line_start:
            # Convert canvas coordinates to image coordinates using stored scaling
            img_x, img_y = self.canvas_to_image_coords(event.x, event.y)
            
            if img_x is not None and img_y is not None:
                self.line_end = (img_x, img_y)
                self.display_image()
    
    def on_canvas_release(self, event):
        if self.current_mode == "line" and self.drawing_line:
            self.drawing_line = False
            self.status_label.config(text="Line drawn! Ready to save evidence.")
    
    def apply_perspective(self):
        if len(self.points) != 4:
            messagebox.showwarning("Warning", "Please select exactly 4 points first!")
            return
            
        if self.processed_image is None:
            return
            
        try:
            # Get original image dimensions
            img_height, img_width = self.processed_image.shape[:2]
            
            # Define source points (the 4 points clicked)
            src_points = np.float32(self.points)
            
            # Calculate the dimensions of the selected rectangle
            x_coords = [p[0] for p in self.points]
            y_coords = [p[1] for p in self.points]
            
            min_x, max_x = min(x_coords), max(x_coords)
            min_y, max_y = min(y_coords), max(y_coords)
            
            rect_width = max_x - min_x
            rect_height = max_y - min_y
            
            # Create destination points for the selected rectangle to become a perfect rectangle
            # But we'll scale this to maintain the same relative size in the final image
            dst_points = np.float32([
                [0, 0],
                [rect_width, 0],
                [rect_width, rect_height],
                [0, rect_height]
            ])
            
            # Calculate perspective transform matrix
            matrix = cv2.getPerspectiveTransform(src_points, dst_points)
            
            # Now we need to calculate where the entire original image will end up
            # Transform all four corners of the original image
            original_corners = np.float32([
                [0, 0],
                [img_width, 0], 
                [img_width, img_height],
                [0, img_height]
            ]).reshape(-1, 1, 2)
            
            transformed_corners = cv2.perspectiveTransform(original_corners, matrix)
            
            # Find the bounding box of the transformed image
            x_coords_new = transformed_corners[:, 0, 0]
            y_coords_new = transformed_corners[:, 0, 1]
            
            min_x_new = np.min(x_coords_new)
            max_x_new = np.max(x_coords_new)
            min_y_new = np.min(y_coords_new)
            max_y_new = np.max(y_coords_new)
            
            # Calculate translation to move everything to positive coordinates
            translation_x = -min_x_new if min_x_new < 0 else 0
            translation_y = -min_y_new if min_y_new < 0 else 0
            
            # Create translation matrix
            translation_matrix = np.array([
                [1, 0, translation_x],
                [0, 1, translation_y],
                [0, 0, 1]
            ], dtype=np.float32)
            
            # Combine the perspective and translation matrices
            final_matrix = translation_matrix @ matrix
            
            # Calculate final output dimensions
            output_width = int(max_x_new - min_x_new + translation_x)
            output_height = int(max_y_new - min_y_new + translation_y)
            
            # Apply the transformation to the entire image
            self.processed_image = cv2.warpPerspective(
                self.processed_image, 
                final_matrix, 
                (output_width, output_height)
            )
            
            # Transform the line points if they exist
            if self.line_start and self.line_end:
                line_points = np.float32([
                    [self.line_start[0], self.line_start[1]],
                    [self.line_end[0], self.line_end[1]]
                ]).reshape(-1, 1, 2)
                
                transformed_line = cv2.perspectiveTransform(line_points, final_matrix)
                self.line_start = (transformed_line[0, 0, 0], transformed_line[0, 0, 1])
                self.line_end = (transformed_line[1, 0, 0], transformed_line[1, 0, 1])
            
            # Reset points since they're no longer relevant
            self.points = []
            
            self.display_image()
            self.status_label.config(text="Perspective corrected! Entire image warped based on selected area.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply perspective correction: {str(e)}")
    
    def reset_points(self):
        self.points = []
        self.display_image()
        self.status_label.config(text="Points reset. Ready for new perspective correction.")
    
    def clear_line(self):
        self.line_start = None
        self.line_end = None
        self.drawing_line = False
        self.display_image()
        self.status_label.config(text="Line cleared. Ready to draw new evidence.")
    
    def save_image(self):
        if self.processed_image is None:
            messagebox.showwarning("Warning", "No image to save!")
            return
            
        file_path = filedialog.asksaveasfilename(
            title="Save your evidence",
            defaultextension=".jpg",
            filetypes=[("JPEG files", "*.jpg"), ("PNG files", "*.png"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                # Draw the line on the image if it exists
                output_image = self.processed_image.copy()
                
                if self.line_start and self.line_end:
                    cv2.line(output_image, 
                            (int(self.line_start[0]), int(self.line_start[1])),
                            (int(self.line_end[0]), int(self.line_end[1])),
                            (0, 0, 255), 3)
                
                cv2.imwrite(file_path, output_image)
                self.status_label.config(text=f"Evidence saved: {os.path.basename(file_path)}")
                messagebox.showinfo("Success", "Your evidence has been preserved for the group chat!")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save image: {str(e)}")

def main():
    root = tk.Tk()
    app = ElbowsChecker(root)
    root.mainloop()

if __name__ == "__main__":
    main()