from tkinter import *
from PIL import Image, ImageTk
import math
import random
import pygame


class Root(Tk):
	def __init__(self):
		super().__init__()
		self.state("zoomed")
		self.title("KCD Lockpicking")
		
		#Sounds
		pygame.mixer.init()
		
		self.click_sound = pygame.mixer.Sound("click.wav")
		self.shuffling_sound = pygame.mixer.Sound("shuffling.wav")
		self.snap_sound = pygame.mixer.Sound("snap.aiff")
		
		self.shuffling_channel = pygame.mixer.Channel(0)
		self.click_channel = pygame.mixer.Channel(1)
		self.snap_channel = pygame.mixer.Channel(2)
		
		#Hide Cursor
		self.config(cursor = "none")
		
		#Canvas
		self.canvas = Canvas(self, bg="#9D8A88")
		self.canvas.pack(fill=BOTH, expand=1)
		self.canvas.update()
		
		can_w = self.canvas.winfo_width()
		can_h = self.canvas.winfo_height()
	
		
		size = min(can_w, can_h)
		
		#Cursor
		cursor_size = int(size * .08)
		
		self.cursor_img = self.resize_image("Cursor.png", cursor_size, cursor_size)
		self.cursor_item = self.canvas.create_image(0, 0, image=self.cursor_img, anchor="center")
		
		self.cursor1_img = self.resize_image("Cursor Highlight.png", cursor_size, cursor_size)
		
		self.canvas.bind("<Motion>", self.update_cursor)
		
		#Lockpick
		self.lockpick_durability = 100
		self.lockpick_broken = False
		
		#Lock
		self.starting_rotation = 0
		self.lock_rotation = 0
		self.rotating = False
		self.rotation_task = None
		self.reverse_rotation_task = None
		self.lock_size = int(size * .60)
		
		
		self.lock_img = self.resize_image("Circular Lock.png", self.lock_size, self.lock_size)
		self.lock_item = self.canvas.create_image(can_w // 2, can_h // 2, image=self.lock_img, anchor="center")
		
		self.sweet_spot_offset = (self.lock_size // 2) - 20
		self.sweet_spot_radius = 50
		
		self.set_sweet_spot()
		
		self.bind("<KeyPress-e>", self.start_rotating)
		self.bind("<KeyRelease-e>", self.stop_rotating)
		
		
	def update_cursor(self, event):
		self.canvas.tag_raise(self.cursor_item)
		
		self.canvas.coords(self.cursor_item, event.x, event.y)
		
		if self.is_near_sweet_spot(event.x, event.y):
			self.canvas.itemconfig(self.cursor_item, image=self.cursor1_img)
			
		else:
			self.canvas.itemconfig(self.cursor_item, image=self.cursor_img)
		
		if not self.shuffling_channel.get_busy():
			self.shuffling_channel.play(self.shuffling_sound, loops=-1)
			
		if hasattr(self, "stop_sound_task"):
			self.after_cancel(self.stop_sound_task)
			
		self.stop_sound_task = self.after(300, self.stop_shuffling_sound)
		
	def stop_shuffling_sound(self):
		if self.shuffling_channel.get_busy():
			self.shuffling_channel.stop()
		
	def set_sweet_spot(self):
		coords = self.canvas.bbox(self.lock_item)
		
		midpoint = self.get_midpoint(
			coords[0],
			coords[1],
			coords[2],
			coords[3],
		)
		
		midpoint_x = midpoint[0]
		midpoint_y = midpoint[1]
		
		if not hasattr(self, "sweet_spot_angle"):
			self.sweet_spot_angle = random.uniform(0, 360)
			self.sweet_spot_distance = random.uniform(0, self.sweet_spot_offset)
		
		rotated_angle = math.radians((self.sweet_spot_angle - self.lock_rotation) % 360)
		
		self.sweet_x = int(midpoint_x + self.sweet_spot_distance * math.cos(rotated_angle))
		self.sweet_y = int(midpoint_y + self.sweet_spot_distance * math.sin(rotated_angle))
		
		radius = self.sweet_spot_radius
		
		if hasattr(self, "sweet_spot"):
			self.canvas.coords(
				self.sweet_spot,
				self.sweet_x - radius, self.sweet_y - radius,
				self.sweet_x + radius, self.sweet_y + radius,
			)
			
		else:
			self.sweet_spot = self.canvas.create_oval(
				self.sweet_x - radius, self.sweet_y - radius,
				self.sweet_x + radius, self.sweet_y + radius,
				outline="yellow",
				fill="yellow",
				width=2,
				state="hidden",
			)
		
	def is_near_sweet_spot(self, x, y, threshold=20):
		return math.sqrt((x - self.sweet_x) ** 2 + (y - self.sweet_y) ** 2) <= threshold
		
	def get_midpoint(self, x, y, x1, y1):
		x2 = (x + x1) / 2
		
		y2 = (y + y1) / 2
		
		return (x2, y2)
		
	def rotate_lock(self, angle):
		new_rotation = (self.lock_rotation + angle)
		
		if new_rotation >= 360:
			new_rotation = 360
			self.lock_rotation = new_rotation
		
			if self.is_unlocked():
				popup = EndPopup(self, True)
				popup.center()
				
				return 
			
		if new_rotation != self.lock_rotation:
			#Lock Rotation
			self.lock_rotation = new_rotation

			rotated_lock = self.og_lock_img.rotate(self.lock_rotation, resample=Image.BICUBIC)
		
			self.lock_img = ImageTk.PhotoImage(rotated_lock)
		
			self.canvas.itemconfig(self.lock_item, image=self.lock_img)
	
			self.set_sweet_spot()
		
	def start_rotating(self, event):
		cursor_coords = self.canvas.coords(self.cursor_item)
		cursor_x, cursor_y = cursor_coords[0], cursor_coords[1]
		
		if not self.rotating and self.is_near_sweet_spot(cursor_x, cursor_y):
			if self.is_near_sweet_spot(cursor_x, cursor_y):
				self.rotating = True
			
				if self.reverse_rotation_task:
					self.after_cancel(self.reverse_rotation_task)
					self.reverse_rotation_task = None
			
			self.rotate_continuous()
			
	def stop_rotating(self, event):
		self.rotating = False
		
		if self.rotation_task:
			self.after_cancel(self.rotation_task)
			self.rotation_task = None
		
		if self.reverse_rotation_task:
			self.after_cancel(self.reverse_rotation_task)
			self.reverse_rotation_task = None
				
		if not self.is_unlocked() and self.lock_rotation > self.starting_rotation:
			self.reverse_rotate()
			
		else:
			self.lock_rotation = self.starting_rotation
			self.rotate_lock(0)
		
	def rotate_continuous(self):
		if self.lockpick_broken:
			return
		
		cursor_coords = self.canvas.coords(self.cursor_item)
		cursor_x, cursor_y = cursor_coords[0], cursor_coords[1]
		
		if self.rotating and self.lock_rotation < 360:
			if self.is_near_sweet_spot(cursor_x, cursor_y):
				self.rotate_lock(3)
				#self.lockpick_durability -= 1
				
			else:
				self.lockpick_durability -= 1
			
			if self.lockpick_durability <= 0:
				self.break_lockpick()
				
				return
			
			self.rotation_task = self.after(16, self.rotate_continuous)
			
		else:
			if not self.lockpick_broken and self.click_channel.get_busy():
				self.click_channel.play(self.click_sound)
			
			self.stop_rotating(None)
			
	def reverse_rotate(self):
		if not self.rotating and self.lock_rotation > self.starting_rotation:
			self.rotate_lock(-2)
			self.reverse_rotation_task = self.after(16, self.reverse_rotate)
			
		else:
			self.lock_rotation = self.starting_rotation
			self.rotate_lock(0)
			
			if self.reverse_rotation_task:
				self.after_cancel(self.reverse_rotation_task)
				self.reverse_rotation_task = None
			
	def is_unlocked(self):
		cursor_coords = self.canvas.coords(self.cursor_item)
		cursor_x, cursor_y = cursor_coords[0], cursor_coords[1]
		
		return self.lock_rotation >= 360 and self.is_near_sweet_spot(cursor_x, cursor_y)
	
	def break_lockpick(self):
		self.lockpick_broken = True
		self.snap_sound.play()
		
		popup = EndPopup(self, False)
		popup.center()
		
	def reset_lock(self):
		if self.reverse_rotation_task:
			self.after_cancel(self.reverse_rotation_task)
			self.reverse_rotation_task = None
		
		self.lockpick_durability = 100
		self.lockpick_broken = False
		
		self.lock_rotation = 0
		#self.rotate_lock(0)
		
		rotated_lock = self.og_lock_img.rotate(self.lock_rotation, resample=Image.BICUBIC)
		self.lock_img = ImageTk.PhotoImage(rotated_lock)
		self.canvas.itemconfig(self.lock_item, image=self.lock_img)
		
		delattr(self, "sweet_spot_angle")
		delattr(self, "sweet_spot_distance")
		self.set_sweet_spot()
		
		self.canvas.update()
		self.update_idletasks()
	
	def resize_image(self, img_path, width, height):
		img = Image.open(img_path)
	
		resized_img = img.resize((width, height), Image.Resampling.LANCZOS)
	
		self.og_lock_img = resized_img
	
		return ImageTk.PhotoImage(resized_img)
		
class EndPopup(Toplevel):
	def __init__(self, parent, success):
		super().__init__(parent)
		
		self.grab_set()
		
		if not success:
			text = "Your lockpick broke!"
			
		else:
			text = "You picked the lock!"
			
		lbl = Label(self, text=text, font=("Times", 30))
		lbl.grid(row=0, column=0, columnspan=2)
		
		retry_btn = Button(self,text="Retry", font=("Times", 25), command=self.retry)
		retry_btn.grid(row=1, column=0)
		
		exit_btn = Button(self,text="Exit", font=("Times", 25), command=parent.destroy)
		exit_btn.grid(row=1, column=1)
		
		self.protocol("WM_DELETE_WINDOW", parent.destroy)
		
	def retry(self):
		self.master.reset_lock()
		
		self.destroy()
		
	def center(self):
		self.update_idletasks()
		
		sw = self.winfo_screenwidth()
		sh = self.winfo_screenheight()
		
		tw = self.winfo_width()
		th = self.winfo_height()
		
		x = (sw // 2) - (tw // 2)
		y = (sh // 2) - (th // 2)
		
		self.geometry(f"{tw}x{th}+{x}+{y}")	
		
		
if __name__ == "__main__":
	root = Root()
	root.mainloop()