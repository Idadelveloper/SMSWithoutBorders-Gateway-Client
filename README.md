##### requirements
* python3
* virtualenv

#### Begin by installing dependencies
```bash
make
make install
```

######Start the API
```bash
source .venv/bin/activate
cd src/
python3 api.py
```
#### Run Daemons
##### To send out SMS messages
```bash
source .venv/bin/activate
cd src/
python3 daemon.py
```
##### To read received SMS messages
```bash
source .venv/bin/activate
cd src/
python3 daemon_received.py
```

#### How to test

##### Send SMS
```bash
./test_script.sh --send <receiving phonenumber>
# example: ./test_script.sh --send 00000000
```
##### See all received SMS messages
```bash
./test_script.sh --received
```
