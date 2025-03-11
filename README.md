
  
# Download

1. Create new directory and copy path
2. Open cmd
3. Run
```
cd path_to_script_directory
```
5. Download repository
```
git clone https://github.com/vaddos689/monad.git
```
6. Go to script directory
```
cd monad
```
7. Create venv Python (required 3.12)
```
py -3.12 -m venv .venv
```
8. Activate venv (windows):
```
.venv\Scripts\activate
```
9. Download libraries:
```
pip install -r requirements.txt
```
# Settings (general_settings.py):
## Main
semaphore - number of simultaneously working accounts
## Apriori
APRIORI_STAKE_RANGE - MON selection range for staking
## Aicraft
AICRAFTREFCODE =  your aicraft refcode for sign-in
AICRAFT_VOTES_COUNT = number of votes per account

# Run:
```
python main.py
```
# Ready modules
1) Aicraft (need proxy)
2) Apriori
3) Balance checker
4) Owlto
5) Kintsu
# Modules in process
1) ?
