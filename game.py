"""坦克大战小游戏。

运行：python game.py
"""

from __future__ import annotations

import math
import random
import tkinter as tk
from dataclasses import dataclass


WIDTH = 900
HEIGHT = 650
FPS_MS = 16

PLAYER_SIZE = 32
ENEMY_SIZE = 30
BULLET_SIZE = 6
PLAYER_SPEED = 4
ENEMY_SPEED = 2
BULLET_SPEED = 8

PLAYER_COLOR = "#2ecc71"
ENEMY_COLOR = "#e74c3c"
WALL_COLOR = "#5d6d7e"
BG_COLOR = "#1b2631"
TEXT_COLOR = "#ecf0f1"


@dataclass
class Tank:
	x: float
	y: float
	size: int
	color: str
	heading: float = 0.0
	hp: int = 1
	shoot_cooldown: int = 0

	@property
	def half(self) -> float:
		return self.size / 2

	def bounds(self) -> tuple[float, float, float, float]:
		half = self.half
		return (self.x - half, self.y - half, self.x + half, self.y + half)


@dataclass
class Bullet:
	x: float
	y: float
	vx: float
	vy: float
	owner: str
	alive: bool = True

	def step(self) -> None:
		self.x += self.vx
		self.y += self.vy
		if self.x < -20 or self.x > WIDTH + 20 or self.y < -20 or self.y > HEIGHT + 20:
			self.alive = False


def rects_overlap(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> bool:
	ax1, ay1, ax2, ay2 = a
	bx1, by1, bx2, by2 = b
	return ax1 < bx2 and ax2 > bx1 and ay1 < by2 and ay2 > by1


def clamp(value: float, low: float, high: float) -> float:
	return max(low, min(high, value))


class TankBattle:
	def __init__(self) -> None:
		self.root = tk.Tk()
		self.root.title("坦克大战")
		self.root.resizable(False, False)

		self.canvas = tk.Canvas(self.root, width=WIDTH, height=HEIGHT, bg=BG_COLOR, highlightthickness=0)
		self.canvas.pack()

		self.keys: set[str] = set()
		self.score = 0
		self.game_over = False
		self.wave = 1

		self.walls = self.build_walls()
		self.player = Tank(WIDTH / 2, HEIGHT - 70, PLAYER_SIZE, PLAYER_COLOR, heading=-90.0, hp=3)
		self.enemies: list[Tank] = []
		self.bullets: list[Bullet] = []

		self.root.bind("<KeyPress>", self.on_key_press)
		self.root.bind("<KeyRelease>", self.on_key_release)
		self.root.bind("<space>", self.fire_player)
		self.root.bind("r", self.restart)
		self.root.bind("R", self.restart)

		self.spawn_wave(self.wave)
		self.loop()

	def build_walls(self) -> list[tuple[float, float, float, float]]:
		return [
			(150, 120, 310, 150),
			(590, 120, 750, 150),
			(220, 240, 260, 430),
			(640, 240, 680, 430),
			(350, 320, 550, 350),
			(160, 500, 350, 530),
			(550, 500, 740, 530),
		]

	def spawn_wave(self, wave: int) -> None:
		count = 2 + wave
		for _ in range(count):
			self.spawn_enemy()

	def spawn_enemy(self) -> None:
		choices = [
			(random.randint(60, WIDTH - 60), 60),
			(60, random.randint(80, HEIGHT // 2)),
			(WIDTH - 60, random.randint(80, HEIGHT // 2)),
		]
		for _ in range(20):
			x, y = random.choice(choices)
			enemy = Tank(float(x), float(y), ENEMY_SIZE, ENEMY_COLOR, heading=90.0, hp=1)
			if not self.collides_with_wall(enemy.bounds()) and not rects_overlap(enemy.bounds(), self.player.bounds()):
				self.enemies.append(enemy)
				return

	def on_key_press(self, event: tk.Event) -> None:
		self.keys.add(event.keysym.lower())

	def on_key_release(self, event: tk.Event) -> None:
		self.keys.discard(event.keysym.lower())

	def fire_player(self, event: tk.Event | None = None) -> None:
		if self.game_over or self.player.shoot_cooldown > 0:
			return
		self.spawn_bullet(self.player, "player")
		self.player.shoot_cooldown = 12

	def spawn_bullet(self, tank: Tank, owner: str) -> None:
		rad = math.radians(tank.heading)
		offset = tank.half + 8
		bx = tank.x + math.cos(rad) * offset
		by = tank.y + math.sin(rad) * offset
		self.bullets.append(
			Bullet(
				bx,
				by,
				math.cos(rad) * BULLET_SPEED,
				math.sin(rad) * BULLET_SPEED,
				owner,
			)
		)

	def collides_with_wall(self, rect: tuple[float, float, float, float]) -> bool:
		return any(rects_overlap(rect, wall) for wall in self.walls)

	def try_move(self, tank: Tank, dx: float, dy: float) -> bool:
		if dx == 0 and dy == 0:
			return False
		old_x, old_y = tank.x, tank.y
		tank.x = clamp(tank.x + dx, tank.half, WIDTH - tank.half)
		tank.y = clamp(tank.y + dy, tank.half + 10, HEIGHT - tank.half)
		rect = tank.bounds()
		if self.collides_with_wall(rect):
			tank.x, tank.y = old_x, old_y
			return False
		return True

	def update_player(self) -> None:
		if self.game_over:
			return

		dx = dy = 0.0
		if "left" in self.keys or "a" in self.keys:
			dx -= PLAYER_SPEED
			self.player.heading = 180.0
		if "right" in self.keys or "d" in self.keys:
			dx += PLAYER_SPEED
			self.player.heading = 0.0
		if "up" in self.keys or "w" in self.keys:
			dy -= PLAYER_SPEED
			self.player.heading = -90.0
		if "down" in self.keys or "s" in self.keys:
			dy += PLAYER_SPEED
			self.player.heading = 90.0

		if dx and dy:
			dx *= 0.7071
			dy *= 0.7071

		self.try_move(self.player, dx, dy)

		if "space" in self.keys:
			self.fire_player()

		if self.player.shoot_cooldown > 0:
			self.player.shoot_cooldown -= 1

	def update_enemies(self) -> None:
		for enemy in self.enemies:
			if enemy.shoot_cooldown > 0:
				enemy.shoot_cooldown -= 1

			dx = self.player.x - enemy.x
			dy = self.player.y - enemy.y
			distance = math.hypot(dx, dy)
			if distance > 1:
				enemy.heading = math.degrees(math.atan2(dy, dx))

			if distance > 170:
				step_x = (dx / distance) * ENEMY_SPEED
				step_y = (dy / distance) * ENEMY_SPEED
				moved = self.try_move(enemy, step_x, step_y)
				if not moved:
					if random.random() < 0.5:
						self.try_move(enemy, step_x, 0)
					else:
						self.try_move(enemy, 0, step_y)
			elif enemy.shoot_cooldown == 0 and random.random() < 0.04:
				self.spawn_bullet(enemy, "enemy")
				enemy.shoot_cooldown = 40

	def update_bullets(self) -> None:
		for bullet in self.bullets:
			if not bullet.alive:
				continue
			bullet.step()

			bullet_rect = (bullet.x - 3, bullet.y - 3, bullet.x + 3, bullet.y + 3)
			if self.collides_with_wall(bullet_rect):
				bullet.alive = False
				continue

			if bullet.owner == "player":
				for enemy in self.enemies:
					if rects_overlap(bullet_rect, enemy.bounds()):
						bullet.alive = False
						enemy.hp -= 1
						if enemy.hp <= 0:
							self.score += 100
							enemy.x = -1000
						break
			else:
				if rects_overlap(bullet_rect, self.player.bounds()):
					bullet.alive = False
					self.player.hp -= 1
					if self.player.hp <= 0:
						self.game_over = True

		self.enemies = [enemy for enemy in self.enemies if enemy.x > -500 and enemy.hp > 0]
		self.bullets = [bullet for bullet in self.bullets if bullet.alive]

	def maybe_next_wave(self) -> None:
		if not self.enemies and not self.game_over:
			self.wave += 1
			self.spawn_wave(self.wave)

	def restart(self, event: tk.Event | None = None) -> None:
		self.score = 0
		self.game_over = False
		self.wave = 1
		self.keys.clear()
		self.player = Tank(WIDTH / 2, HEIGHT - 70, PLAYER_SIZE, PLAYER_COLOR, heading=-90.0, hp=3)
		self.enemies = []
		self.bullets = []
		self.spawn_wave(self.wave)

	def draw_tank(self, tank: Tank) -> None:
		x1, y1, x2, y2 = tank.bounds()
		self.canvas.create_rectangle(x1, y1, x2, y2, fill=tank.color, outline="")
		self.canvas.create_oval(x1 + 4, y1 + 4, x2 - 4, y2 - 4, outline="#ffffff", width=1)

		rad = math.radians(tank.heading)
		barrel_len = tank.half + 10
		bx = tank.x + math.cos(rad) * barrel_len
		by = tank.y + math.sin(rad) * barrel_len
		self.canvas.create_line(tank.x, tank.y, bx, by, fill="#f8f9f9", width=4, capstyle=tk.ROUND)

	def draw(self) -> None:
		self.canvas.delete("all")

		for wall in self.walls:
			self.canvas.create_rectangle(*wall, fill=WALL_COLOR, outline="")

		for bullet in self.bullets:
			self.canvas.create_oval(
				bullet.x - BULLET_SIZE / 2,
				bullet.y - BULLET_SIZE / 2,
				bullet.x + BULLET_SIZE / 2,
				bullet.y + BULLET_SIZE / 2,
				fill="#f1c40f" if bullet.owner == "player" else "#ffb3b3",
				outline="",
			)

		self.draw_tank(self.player)
		for enemy in self.enemies:
			self.draw_tank(enemy)

		self.canvas.create_text(
			12,
			12,
			anchor="nw",
			fill=TEXT_COLOR,
			font=("Arial", 14, "bold"),
			text=f"分数: {self.score}    关卡: {self.wave}    生命: {self.player.hp}",
		)
		self.canvas.create_text(
			WIDTH - 12,
			12,
			anchor="ne",
			fill=TEXT_COLOR,
			font=("Arial", 12),
			text="方向键/WASD移动，空格射击，R重新开始",
		)

		if self.game_over:
			self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#000000", stipple="gray25", outline="")
			self.canvas.create_text(
				WIDTH / 2,
				HEIGHT / 2 - 30,
				fill="#ffffff",
				font=("Arial", 28, "bold"),
				text="游戏结束",
			)
			self.canvas.create_text(
				WIDTH / 2,
				HEIGHT / 2 + 20,
				fill="#ffffff",
				font=("Arial", 16),
				text="按 R 重新开始",
			)

	def loop(self) -> None:
		if not self.game_over:
			self.update_player()
			self.update_enemies()
			self.update_bullets()
			self.maybe_next_wave()

		self.draw()
		self.root.after(FPS_MS, self.loop)

	def run(self) -> None:
		self.root.mainloop()


if __name__ == "__main__":
	TankBattle().run()
