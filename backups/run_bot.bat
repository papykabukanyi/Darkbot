@echo off
TITLE Darkbot - Sneaker Deal Finder (MongoDB)
echo Starting Darkbot with MongoDB storage...
cd /d C:\Users\lovingtracktor\Desktop\Darkbot
python main.py --continuous --interval 30 --sites sneakers champssports footlocker idsports nike adidas newbalance puma reebok finishline jdsports eastbay --mongodb --iterate
pause
