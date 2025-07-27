# PowerShell script to run the sneaker bot with MongoDB storage

# Change to the project directory
cd C:\Users\lovingtracktor\Desktop\Darkbot

# Activate virtual environment if you have one
# .\venv\Scripts\Activate

# Run the bot with MongoDB storage and continuous mode
python main.py --continuous --interval 30 --sites sneakers champssports footlocker idsports nike adidas newbalance puma reebok finishline jdsports eastbay --mongodb --iterate

# If you want to run with more sites, uncomment this line:
# python main.py --continuous --interval 30 --mongodb --iterate

# Pause at the end
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
