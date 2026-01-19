import ast,base64,cv2,json,time
from flask import Flask,redirect,render_template,request,url_for
import fgoDevice
import fgoKernel
from fgoLogging import getLogger
from fgoTeamupParser import IniParser
logger=getLogger('Web')

teamup=IniParser('fgoTeamup.ini')
app=Flask(__name__,static_folder='fgoWebUI',template_folder='fgoWebUI')

@app.route('/')
def root():
    return redirect('/index')

@app.route('/index')
def index():
    return render_template('index.html',teamups=teamup.sections(),config=config,device=fgoDevice.device.name)

@app.route('/api/connect',methods=['POST'])
def connect():
    serial=request.form.get('serial')
    if not serial:
        return 'Serial not provided',400
    fgoDevice.device=fgoDevice.Device(serial)
    return fgoDevice.device.name or 'Connection failed'

@app.route('/api/teamup/load',methods=['POST'])
def teamupLoad():
    teamName=request.form.get('teamName')
    if not teamName or teamName not in teamup:
        return 'Team not found',404
    try:
        return {i:ast.literal_eval(j)for i,j in teamup[teamName].items()}
    except (ValueError,SyntaxError) as e:
        logger.error(f'Failed to parse team {teamName}: {e}')
        return 'Invalid team data',500

@app.route('/api/teamup/save',methods=['POST'])
def teamupSave():
    teamName=request.form.get('teamName')
    data=request.form.get('data')
    if not teamName or not data:
        return 'Missing teamName or data',400
    try:
        teamup[teamName]=json.loads(data)
        with open('fgoTeamup.ini','w')as f:
            teamup.write(f)
        return 'Saved'
    except json.JSONDecodeError as e:
        return f'Invalid JSON: {e}',400
    except (OSError,PermissionError) as e:
        logger.error(f'Failed to save teamup: {e}')
        return 'Save failed',500

@app.route('/api/apply',methods=['POST'])
def apply():
    try:
        data=json.loads(request.form.get('data','{}'))
        fgoKernel.Main.teamIndex=data.get('teamIndex',0)
        fgoKernel.ClassicTurn.skillInfo=data.get('skillInfo',fgoKernel.ClassicTurn.skillInfo)
        fgoKernel.ClassicTurn.houguInfo=data.get('houguInfo',fgoKernel.ClassicTurn.houguInfo)
        fgoKernel.ClassicTurn.masterSkill=data.get('masterSkill',fgoKernel.ClassicTurn.masterSkill)
        return 'Applied'
    except json.JSONDecodeError as e:
        return f'Invalid JSON: {e}',400
    except (KeyError,TypeError) as e:
        return f'Invalid data format: {e}',400

@app.route('/api/run/main',methods=['POST'])
def runMain():
    if not fgoDevice.device.available:
        return 'Device not available'
    fgoKernel.Main(**{i:int(j)for i,j in request.form.items()})()
    return 'Done'

@app.route('/api/run/battle',methods=['POST'])
def runBattle():
    if not fgoDevice.device.available:
        return 'Device not available'
    fgoKernel.Battle()()
    return 'Done'

@app.route('/api/run/classic',methods=['POST'])
def runClassic():
    if not fgoDevice.device.available:
        return 'Device not available'
    fgoKernel.Main(**{i:int(j)for i,j in request.form.items()},battleClass=lambda:fgoKernel.Battle(fgoKernel.ClassicTurn))()
    return 'Done'

@app.route('/api/pause',methods=['POST'])
def pause():
    fgoKernel.schedule.pause()
    return 'Paused'

@app.route('/api/stop',methods=['POST'])
def stop():
    fgoKernel.schedule.stop()
    return 'Stopped'

@app.route('/api/stopLater',methods=['POST'])
def stopLater():
    try:
        value=int(request.form.get('value',0))
        fgoKernel.schedule.stopLater(value)
        return f'Will stop after {value} battles'
    except ValueError:
        return 'Invalid value',400

@app.route('/api/screenshot',methods=['POST'])
def screenshot():
    if not fgoDevice.device.available:
        return 'Device not available',503
    try:
        det=fgoKernel.Detect()
        success,encoded=cv2.imencode('.png',det.im)
        if not success:
            return 'Encoding failed',500
        return base64.b64encode(encoded.tobytes())
    except Exception as e:
        logger.error(f'Screenshot failed: {e}')
        return 'Screenshot failed',500

@app.route('/api/bench',methods=['POST'])
def bench():
    if not fgoDevice.device.available:
        return 'Device not available'
    result=fgoKernel.bench(15)
    parts=[]
    if result.get('touch'):parts.append(f"点击 {result['touch']:.2f}ms")
    if result.get('screenshot'):parts.append(f"截图 {result['screenshot']:.2f}ms")
    return ', '.join(parts) if parts else 'No benchmark data'

def main(config):
    globals()['config']=config
    app.run(host='0.0.0.0', port='15000')
