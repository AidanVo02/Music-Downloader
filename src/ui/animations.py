"""
Enhanced Loading Animations for Music Downloader
- 3D Bouncing Sphere with Particle Effects
- Real-time animation with pulsing and color transitions
"""

import math
import random
import customtkinter as ctk
from tkinter import Canvas

class LoadingAnimation:
    """3D Bouncing Sphere with Particle Effects"""
    
    def __init__(self, canvas: Canvas, canvas_width=300, canvas_height=150):
        self.canvas = canvas
        self.width = canvas_width
        self.height = canvas_height
        self.is_running = False
        self.frame = 0
        
        # Sphere properties
        self.sphere_x = canvas_width / 2
        self.sphere_y = canvas_height / 2
        self.sphere_radius = 20
        self.vx = 3.5
        self.vy = 2.5
        self.gravity = 0.15
        
        # Particle system
        self.particles = []
        self.max_particles = 30
        
        # Colors
        self.base_colors = ["#0ea5e9", "#a78bfa", "#22c55e", "#f59e0b", "#ec4899"]
        self.current_color_idx = 0
        
        # Animation settings
        self.animation_speed = 50  # milliseconds
        self.pulse_intensity = 0
        self.pulse_direction = 1
    
    def start(self):
        """Start the animation"""
        self.is_running = True
        self.frame = 0
        self.particles.clear()
        self._animate()
    
    def stop(self):
        """Stop the animation"""
        self.is_running = False
    
    def _animate(self):
        """Main animation loop"""
        if not self.is_running:
            return
        
        self.frame += 1
        
        # Clear canvas
        self.canvas.delete("all")
        
        # Update sphere position with bounce physics
        self._update_sphere()
        
        # Update particles
        self._update_particles()
        
        # Draw particles
        self._draw_particles()
        
        # Draw sphere with 3D effect
        self._draw_sphere()
        
        # Draw loading text
        self._draw_loading_text()
        
        # Schedule next frame
        if self.is_running:
            self.canvas.after(self.animation_speed, self._animate)
    
    def _update_sphere(self):
        """Update sphere position with physics"""
        # Apply gravity
        self.vy += self.gravity
        
        # Update position
        self.sphere_x += self.vx
        self.sphere_y += self.vy
        
        # Bounce off walls
        if self.sphere_x - self.sphere_radius < 10:
            self.sphere_x = 10 + self.sphere_radius
            self.vx = abs(self.vx) * 0.9
        elif self.sphere_x + self.sphere_radius > self.width - 10:
            self.sphere_x = self.width - 10 - self.sphere_radius
            self.vx = -abs(self.vx) * 0.9
        
        # Bounce off floor
        if self.sphere_y + self.sphere_radius > self.height - 10:
            self.sphere_y = self.height - 10 - self.sphere_radius
            self.vy = -abs(self.vy) * 0.85
            
            # Create particles on bounce
            self._create_bounce_particles()
            
            # Add random horizontal movement for variety
            self.vx += random.uniform(-1, 1)
        
        # Bounce off ceiling
        if self.sphere_y - self.sphere_radius < 10:
            self.sphere_y = 10 + self.sphere_radius
            self.vy = abs(self.vy) * 0.9
        
        # Update pulse animation
        self.pulse_intensity += self.pulse_direction * 0.05
        if self.pulse_intensity > 1:
            self.pulse_intensity = 1
            self.pulse_direction = -1
        elif self.pulse_intensity < 0:
            self.pulse_intensity = 0
            self.pulse_direction = 1
        
        # Change color every 60 frames
        if self.frame % 60 == 0:
            self.current_color_idx = (self.current_color_idx + 1) % len(self.base_colors)
    
    def _create_bounce_particles(self):
        """Create particles on sphere bounce"""
        num_particles = random.randint(8, 12)
        for _ in range(num_particles):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1, 4)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed - 2  # Bias upward
            
            particle = {
                'x': self.sphere_x,
                'y': self.sphere_y,
                'vx': vx,
                'vy': vy,
                'life': 1.0,
                'max_life': 1.0,
                'size': random.randint(2, 6),
                'color': self.base_colors[self.current_color_idx]
            }
            self.particles.append(particle)
    
    def _update_particles(self):
        """Update particle system"""
        for particle in self.particles[:]:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['vy'] += 0.1  # Gravity on particles
            particle['life'] -= 0.02
            
            if particle['life'] <= 0:
                self.particles.remove(particle)
        
        # Keep particle count reasonable
        while len(self.particles) > self.max_particles:
            self.particles.pop(0)
    
    def _draw_particles(self):
        """Draw all particles"""
        for particle in self.particles:
            alpha = int(255 * particle['life'])
            # Simple particle: small circles
            x = particle['x']
            y = particle['y']
            size = particle['size'] * (particle['life'] ** 0.5)
            
            try:
                self.canvas.create_oval(
                    x - size, y - size,
                    x + size, y + size,
                    fill=particle['color'],
                    outline=""
                )
            except:
                pass
    
    def _draw_sphere(self):
        """Draw 3D sphere with gradient effect"""
        x = self.sphere_x
        y = self.sphere_y
        r = self.sphere_radius
        
        # Calculate pulsed radius
        pulsed_radius = r * (1 + self.pulse_intensity * 0.2)
        
        color = self.base_colors[self.current_color_idx]
        
        # Draw outer sphere (shadow)
        self.canvas.create_oval(
            x - pulsed_radius - 2, y - pulsed_radius + 15,
            x + pulsed_radius + 2, y + pulsed_radius + 20,
            fill="gray20", outline="gray30"
        )
        
        # Draw main sphere
        self.canvas.create_oval(
            x - pulsed_radius, y - pulsed_radius,
            x + pulsed_radius, y + pulsed_radius,
            fill=color, outline=color
        )
        
        # Draw highlight for 3D effect
        highlight_radius = pulsed_radius * 0.4
        self.canvas.create_oval(
            x - highlight_radius * 0.6, y - highlight_radius * 0.8,
            x - highlight_radius * 0.1, y - highlight_radius * 0.3,
            fill="white", outline=""
        )
        
        # Draw inner shine
        shine_radius = pulsed_radius * 0.6
        self.canvas.create_oval(
            x - shine_radius * 0.2, y - shine_radius * 0.3,
            x + shine_radius * 0.2, y + shine_radius * 0.1,
            fill="white", outline="", state="normal"
        )
    
    def _draw_loading_text(self):
        """Draw "Loading" text with animation"""
        dots = "." * ((self.frame // 20) % 4)
        text = "Loading" + dots
        
        try:
            self.canvas.create_text(
                self.width / 2, self.height - 20,
                text=text, font=("Segoe UI", 12, "bold"),
                fill=self.base_colors[self.current_color_idx]
            )
        except:
            pass


class AnalyzingAnimation:
    """Pulsing sphere animation for BPM/Key analysis"""
    
    def __init__(self, canvas: Canvas, canvas_width=300, canvas_height=150):
        self.canvas = canvas
        self.width = canvas_width
        self.height = canvas_height
        self.is_running = False
        self.frame = 0
        self.center_x = canvas_width / 2
        self.center_y = canvas_height / 2
        self.base_radius = 25
        self.animation_speed = 50
        self.color_cycle = 0
        
        # Ring effect
        self.rings = []
    
    def start(self):
        """Start the analyzing animation"""
        self.is_running = True
        self.frame = 0
        self.rings = []
        self._animate()
    
    def stop(self):
        """Stop the animation"""
        self.is_running = False
    
    def _animate(self):
        """Main animation loop"""
        if not self.is_running:
            return
        
        self.frame += 1
        
        # Clear canvas
        self.canvas.delete("all")
        
        # Create expanding rings
        self._update_rings()
        
        # Draw rings
        self._draw_rings()
        
        # Draw central sphere
        self._draw_central_sphere()
        
        # Draw text
        self._draw_analyzing_text()
        
        if self.is_running:
            self.canvas.after(self.animation_speed, self._animate)
    
    def _update_rings(self):
        """Update expanding ring effects"""
        # Add new ring every 15 frames
        if self.frame % 15 == 0:
            self.rings.append({'age': 0, 'max_age': 60})
        
        # Update existing rings
        for ring in self.rings[:]:
            ring['age'] += 1
            if ring['age'] >= ring['max_age']:
                self.rings.remove(ring)
    
    def _draw_rings(self):
        """Draw concentric expanding rings"""
        colors = ["#0ea5e9", "#a78bfa", "#22c55e", "#f59e0b", "#ec4899"]
        
        for i, ring in enumerate(self.rings):
            progress = ring['age'] / ring['max_age']
            radius = self.base_radius + (100 * progress)
            alpha = int(255 * (1 - progress))
            color = colors[i % len(colors)]
            
            # Draw expanding ring
            try:
                self.canvas.create_oval(
                    self.center_x - radius, self.center_y - radius,
                    self.center_x + radius, self.center_y + radius,
                    outline=color, width=2, state="normal"
                )
            except:
                pass
    
    def _draw_central_sphere(self):
        """Draw pulsing central sphere"""
        pulse = math.sin(self.frame * 0.1) * 0.3 + 0.7
        radius = self.base_radius * pulse
        
        colors = ["#0ea5e9", "#a78bfa", "#22c55e", "#f59e0b", "#ec4899"]
        color_idx = (self.frame // 30) % len(colors)
        color = colors[color_idx]
        
        # Draw sphere
        self.canvas.create_oval(
            self.center_x - radius, self.center_y - radius,
            self.center_x + radius, self.center_y + radius,
            fill=color, outline=color
        )
        
        # Draw highlight
        highlight_radius = radius * 0.4
        self.canvas.create_oval(
            self.center_x - highlight_radius, self.center_y - highlight_radius * 1.2,
            self.center_x - highlight_radius * 0.3, self.center_y - highlight_radius * 0.5,
            fill="white", outline=""
        )
    
    def _draw_analyzing_text(self):
        """Draw analyzing text with animation"""
        dots = "." * ((self.frame // 20) % 4)
        text = "Analyzing" + dots
        
        try:
            self.canvas.create_text(
                self.width / 2, self.height - 20,
                text=text, font=("Segoe UI", 12, "bold"),
                fill="#a78bfa"
            )
        except:
            pass


class ParticleExplosion:
    """One-time particle explosion effect"""
    
    def __init__(self, canvas: Canvas, x: float, y: float, canvas_width=300, canvas_height=150):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.width = canvas_width
        self.height = canvas_height
        self.particles = []
        self.is_running = False
        self.animation_speed = 30
        
        self._create_particles()
    
    def _create_particles(self):
        """Create explosion particles"""
        num_particles = 20
        colors = ["#0ea5e9", "#a78bfa", "#22c55e", "#f59e0b", "#ec4899"]
        
        for _ in range(num_particles):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 6)
            
            particle = {
                'x': self.x,
                'y': self.y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'life': 1.0,
                'size': random.randint(3, 8),
                'color': random.choice(colors)
            }
            self.particles.append(particle)
    
    def start(self):
        """Start the explosion animation"""
        self.is_running = True
        self._animate()
    
    def stop(self):
        """Stop the animation"""
        self.is_running = False
    
    def _animate(self):
        """Animate particles"""
        if not self.is_running or not self.particles:
            self.is_running = False
            return
        
        self.canvas.delete("all")
        
        # Update particles
        for particle in self.particles[:]:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['vy'] += 0.15  # Gravity
            particle['life'] -= 0.04
            
            if particle['life'] <= 0:
                self.particles.remove(particle)
        
        # Draw particles
        for particle in self.particles:
            x = particle['x']
            y = particle['y']
            size = particle['size'] * particle['life']
            
            try:
                self.canvas.create_oval(
                    x - size, y - size,
                    x + size, y + size,
                    fill=particle['color'],
                    outline=""
                )
            except:
                pass
        
        if self.is_running and self.particles:
            self.canvas.after(self.animation_speed, self._animate)


# ============= HELPER FUNCTION =============

def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(r, g, b):
    """Convert RGB tuple to hex color"""
    return f"#{r:02x}{g:02x}{b:02x}"
