$readme = @'
# Campus Canteen Pre-Ordering System

Students order food from their phones, canteen staff manage orders, and an SMS says when the order is ready for pickup.

## Features

1. Browse the menu
2. Place an order
3. Track order status
4. Staff dashboard
5. SMS order-ready alert (Africa's Talking)

## Run it

    python -m venv venv
    venv\Scripts\activate
    pip install -r requirements.txt
    python app.py

## Run the tests

    pytest -v

## Team

- Yasim22
'@
[System.IO.File]::WriteAllText((Join-Path (Get-Location).Path "README.md"), $readme, (New-Object System.Text.UTF8Encoding $false))
git add .
git commit -m "Add README"
git push
