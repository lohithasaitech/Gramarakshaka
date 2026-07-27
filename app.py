import os
import sqlite3
import requests
import base64
import threading
import time
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

base_dir = os.path.dirname(os.path.abspath(__file__))
kalyan_db_path = os.path.join(base_dir, 'gramrakshak.db')

bot_token = "BOT_TOKEn"
admin_chat_ids = ["USER_ID"]

def init_kalyan_db():
    try:
        conn = sqlite3.connect(kalyan_db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS alerts (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, lat REAL, lng REAL, timestamp TEXT, status TEXT, user_id TEXT)''')
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB Init Error: {e}")

init_kalyan_db()

def dispatch_alert_by_kalyan(sos_type, lat, lng, victim, img_front, img_back):
    maps_link = f"https://www.google.com/maps?q={lat},{lng}"
    clean_type = sos_type.replace("_", " ") 
    
    alert_msg = f"🚨 <b>GRAMRAKSHAK EMERGENCY ALERT</b> 🚨\n\n🆘 <b>Type:</b> {clean_type}\n👤 <b>Victim:</b> {victim}\n⏰ <b>Time:</b> {datetime.now().strftime('%I:%M %p')}\n📍 <b>Location:</b> <a href='{maps_link}'>Click to Open Map</a>\n\n<i>~ System Dispatched by TEAM SBL</i>"
    
    def decode_image(img_data):
        if img_data:
            try:
                if "," in img_data:
                    img_data = img_data.split(",")[1]
                return base64.b64decode(img_data)
            except Exception:
                pass
        return None

    front_bytes = decode_image(img_front)
    back_bytes = decode_image(img_back)

    for chat_id in admin_chat_ids:
        def push_to_telegram(cid):
            url_photo = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
            url_text = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            
            if front_bytes:
                requests.post(url_photo, data={'chat_id': cid, 'caption': alert_msg, 'parse_mode': 'HTML'}, files={'photo': ('front_cam.jpg', front_bytes, 'image/jpeg')}, timeout=15)
            else:
                requests.post(url_text, json={"chat_id": cid, "text": alert_msg, "parse_mode": "HTML"}, timeout=10)

            if back_bytes:
                back_caption = "📸 <b>Back Camera View</b>\n<i>~ Curated Intelligence by TEAM SBL</i>"
                requests.post(url_photo, data={'chat_id': cid, 'caption': back_caption, 'parse_mode': 'HTML'}, files={'photo': ('back_cam.jpg', back_bytes, 'image/jpeg')}, timeout=15)
                        
        threading.Thread(target=push_to_telegram, args=(chat_id,)).start()

@app.route('/api/sos', methods=['POST'])
def trigger_emergency():
    req = request.json
    lat = req.get('lat', 0.0)
    lng = req.get('lng', 0.0)
    sos_type = req.get('type', 'GENERAL SOS')
    user = req.get('user', 'Unknown')
    img_front = req.get('image_front', None)
    img_back = req.get('image_back', None)
    timestamp = datetime.now().strftime("%Y-%m-%d %I:%M %p")
    
    try:
        conn = sqlite3.connect(kalyan_db_path)
        c = conn.cursor()
        c.execute("INSERT INTO alerts (type, lat, lng, timestamp, status, user_id) VALUES (?, ?, ?, ?, ?, ?)", (sos_type, lat, lng, timestamp, "ACTIVE", user))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB Insert Fail: {e}")
    
    bg_task = threading.Thread(target=dispatch_alert_by_kalyan, args=(sos_type, lat, lng, user, img_front, img_back))
    bg_task.start()
    
    return jsonify({"status": "success", "msg": "alert_dispatched"})

@app.route('/api/alerts', methods=['GET'])
def get_kalyan_system_alerts():
    try:
        conn = sqlite3.connect(kalyan_db_path)
        c = conn.cursor()
        c.execute("SELECT id, type, lat, lng, timestamp, status, user_id FROM alerts ORDER BY id DESC")
        records = c.fetchall()
        conn.close()
        
        response_data = []
        for row in records:
            response_data.append({
                "id": row[0], "type": row[1], "lat": row[2], "lng": row[3],
                "timestamp": row[4], "status": row[5], "user_id": row[6]
            })
        return jsonify({"status": "success", "data": response_data})
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)})

UI_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>GramRakshak by TEAM SBL</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script crossorigin src="https://unpkg.com/react@18/umd/react.development.js"></script>
    <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <style>
        body { background: #030712; color: white; font-family: sans-serif; overflow: hidden; background-image: radial-gradient(circle at top, #3f0000 0%, #030712 60%); height: 100vh;}
        .glass { background: rgba(15, 23, 42, 0.95); border: 1px solid rgba(255,255,255,0.1); }
        .sos-btn { background: linear-gradient(135deg, #ef4444, #991b1b); box-shadow: 0 0 30px rgba(239, 68, 68, 0.6); }
        .sos-btn:active { transform: scale(0.92); }
        .nav-item { color: #64748b; transition: all 0.3s; }
        .nav-item.active { color: #ef4444; transform: scale(1.1); }
        ::-webkit-scrollbar { display: none; }
        .dot-flashing { position: relative; width: 8px; height: 8px; border-radius: 5px; background-color: #ef4444; animation: dot-flashing 1s infinite linear alternate; animation-delay: 0.5s; }
        .dot-flashing::before, .dot-flashing::after { content: ''; display: inline-block; position: absolute; top: 0; }
        .dot-flashing::before { left: -12px; width: 8px; height: 8px; border-radius: 5px; background-color: #ef4444; animation: dot-flashing 1s infinite alternate; animation-delay: 0s; }
        .dot-flashing::after { left: 12px; width: 8px; height: 8px; border-radius: 5px; background-color: #ef4444; animation: dot-flashing 1s infinite alternate; animation-delay: 1s; }
        @keyframes dot-flashing { 0% { background-color: #ef4444; } 50%, 100% { background-color: rgba(239, 68, 68, 0.2); } }
        @keyframes pulse-red { 0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); } 70% { box-shadow: 0 0 0 25px rgba(239, 68, 68, 0); } 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); } }
        .sos-anim { animation: pulse-red 2s infinite; }
        .hover-anim { transition: transform 0.2s; }
        .hover-anim:active { transform: scale(0.92); }
    </style>
</head>
<body>
    <div id="root"></div>
    <script type="text/babel">
        
        console.log("GramRakshak UI Initialized - Code by TEAM SBL");

        const KalyanDeviceHelper = {
            fetchGPS: () => {
                return new Promise((res, rej) => {
                    if (!navigator.geolocation) return rej(new Error("No GPS Module"));
                    navigator.geolocation.getCurrentPosition(
                        (pos) => res({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
                        (err) => rej(err),
                        { enableHighAccuracy: true } 
                    );
                });
            },
            captureMedia: async (facingMode) => {
                return new Promise(async (res, rej) => {
                    try {
                        const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: facingMode } }, audio: false });
                        const vid_node = document.createElement('video');
                        vid_node.setAttribute('autoplay', '');
                        vid_node.setAttribute('playsinline', '');
                        vid_node.muted = true; 
                        vid_node.srcObject = stream;
                        
                        vid_node.onloadedmetadata = () => {
                            vid_node.play().catch(()=>{});
                            setTimeout(() => {
                                try {
                                    const cvs = document.createElement('canvas');
                                    cvs.width = vid_node.videoWidth || 320;
                                    cvs.height = vid_node.videoHeight || 480;
                                    cvs.getContext('2d').drawImage(vid_node, 0, 0, cvs.width, cvs.height);
                                    const img_payload = cvs.toDataURL('image/jpeg', 0.4); 
                                    stream.getTracks().forEach(t => t.stop()); 
                                    res(img_payload);
                                } catch(e) {
                                    stream.getTracks().forEach(t => t.stop());
                                    rej(e);
                                }
                            }, 800); 
                        };
                    } catch (err) { rej(err); }
                });
            }
        };

        const { useState, useEffect, useRef } = React;
        
        const auth_token = "API_TOKEN";
        const ai_models = ["ENTER_MODEL_NAME"];

        function GramRakshakApp() {
            const [user, setUser] = useState(null);
            const [tab, setTab] = useState('home');
            const [loc, setLoc] = useState({ lat: null, lng: null });
            
            const [chatBox, setChatBox] = useState([{ sender: 'ai', text: "Namaste! Nenu GramRakshak AI ni. Meeku emaina emergency help kavalante adagandi." }]);
            const [msgInput, setMsgInput] = useState('');
            const [aiLoading, setAiLoading] = useState(false);
            const [isDispatching, setIsDispatching] = useState(false);
            const scrollRef = useRef(null);

            const [adminAuth, setAdminAuth] = useState(false);
            const [adminId, setAdminId] = useState('');
            const [adminKey, setAdminKey] = useState('');
            const [dbRecords, setDbRecords] = useState([]);
            const [loadingRecords, setLoadingRecords] = useState(false);

            useEffect(() => { scrollRef.current?.scrollIntoView({ behavior: "smooth" }); }, [chatBox]);

            useEffect(() => {
                if(tab === 'admin' && adminAuth) {
                    sync_admin_data();
                }
            }, [tab, adminAuth]);

            const authenticate_user = () => {
                const phone_val = document.getElementById('phone_input').value;
                
                const validPhoneRegex = /^[6-9]\d{9}$/;
                if (!validPhoneRegex.test(phone_val)) {
                    alert("please enter correct phone number");
                    return;
                }

                const isRepeating = /^(\d)\1{9}$/.test(phone_val);
                if (isRepeating) {
                    alert("please enter correct phone number");
                    return;
                }

                const blockedNumbers = ['1234567890', '0987654321', '9876543210', '0123456789'];
                if (blockedNumbers.includes(phone_val)) {
                    alert("please enter correct phone number");
                    return;
                }

                setUser(phone_val); 
            };

            const fire_sos_alert = async (emergency_type) => {
                setIsDispatching(true);
                let currentLat = null, currentLng = null;
                let photoFront = null, photoBack = null;

                try {
                    const pos = await KalyanDeviceHelper.fetchGPS();
                    currentLat = pos.lat; currentLng = pos.lng;
                    setLoc({lat: currentLat, lng: currentLng});
                } catch(err) {
                    setIsDispatching(false);
                    alert("Location Block aindi.\\nURL bar lo 'Lock ' icon nokki Location ni 'Allow' cheyandi.");
                    return; 
                }

                if (emergency_type === 'EMERGENCY SOS') {
                    try { 
                        photoFront = await KalyanDeviceHelper.captureMedia('user'); 
                    } catch(e) { console.log("Front cam err"); }
                    
                    await new Promise(r => setTimeout(r, 400));
                    
                    try { 
                        photoBack = await KalyanDeviceHelper.captureMedia('environment'); 
                    } catch(e) { console.log("Back cam err"); }
                }

                try { new Audio('https://www.soundjay.com/misc/sounds/emergency-alarm-with-reverb-1.mp3').play().catch(()=>{}); } catch(e){}
                
                try {
                    const res = await fetch('/api/sos', { 
                        method: 'POST', 
                        headers: {'Content-Type': 'application/json'}, 
                        body: JSON.stringify({ 
                            lat: currentLat, lng: currentLng, 
                            type: emergency_type, user: user, 
                            image_front: photoFront, 
                            image_back: photoBack 
                        }) 
                    });
                    
                    if(res.ok){
                        alert(`✅ ${emergency_type.replace('_', ' ')} Alert Dispatched!\\nMeeru safe ga undandi, ma team vasthundi.`);
                        if(adminAuth) sync_admin_data(); 
                    } else {
                        alert(" Alert processing... (Network Slow)");
                    }
                } catch(e) {
                    alert(" Offline: SMS will be sent when connection restores.");
                } finally {
                    setIsDispatching(false);
                }
            };

            const handle_ai_chat = async () => {
                if(!msgInput) return;
                const user_text = msgInput;
                setChatBox(p => [...p, { sender: 'user', text: user_text }]);
                setMsgInput(''); setAiLoading(true);
                
                let success_flag = false, final_reply = "";
                const sys_prompt = `Act as an emergency rural assistant for India. Answer ONLY in Tanglish (Telugu language written in English alphabet). Do NOT use Telugu script. Keep it under 3 sentences. Be professional. User question: ${user_text}`;

                for (const model of ai_models) {
                    try {
                        const ai_req = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${auth_token}`, {
                            method: 'POST', headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ contents: [{ parts: [{ text: sys_prompt }] }] })
                        });
                        if (ai_req.ok) {
                            const ai_data = await ai_req.json();
                            final_reply = ai_data.candidates[0].content.parts[0].text;
                            success_flag = true; break;
                        }
                    } catch (e) {}
                }

                if (success_flag) setChatBox(p => [...p, { sender: 'ai', text: final_reply }]);
                else setTimeout(() => { setChatBox(p => [...p, { sender: 'ai', text: "Server busy ga undi bro. Emergency ayite 108 ki call cheyandi." }]); }, 500);
                setAiLoading(false);
            };

            const verify_admin = () => {
                if(adminId === 'admin' && adminKey === 'Lohitha@123') {
                    setAdminAuth(true);
                } else {
                    alert(" Invalid Username or Password!");
                }
            };

            const sync_admin_data = async () => {
                setLoadingRecords(true);
                try {
                    const res = await fetch('/api/alerts');
                    const data = await res.json();
                    if(data.status === 'success') {
                        setDbRecords(data.data);
                    }
                } catch(e) {
                    console.error("fetch_err", e);
                }
                setLoadingRecords(false);
            };

            if(!user) {
                return (
                    <div className="h-screen flex flex-col items-center justify-center p-6 bg-slate-950">
                        <div className="w-24 h-24 bg-red-600 rounded-3xl flex items-center justify-center mb-6 shadow-[0_0_30px_rgba(239,68,68,0.5)]">
                            <i className="fas fa-shield-halved text-5xl text-white"></i>
                        </div>
                        <h1 className="text-4xl font-black mb-2 tracking-tighter text-white">GRAMRAKSHAK</h1>
                        <p className="mb-10 text-slate-400 text-xs font-bold text-center uppercase tracking-widest">Rural Emergency System<br/><span className="text-red-500 mt-1 inline-block">DEVELOPED BY TEAM SBL</span></p>
                        <div className="glass w-full p-8 rounded-[2rem]">
                            <label className="text-[10px] text-slate-400 font-black uppercase mb-2 block">Mobile / ID</label>
                            <input id="phone_input" type="number" className="w-full bg-slate-800 p-4 rounded-xl mb-6 outline-none text-white font-bold" placeholder="Enter Your Number" />
                            <button onClick={authenticate_user} className="w-full bg-red-600 py-4 rounded-xl font-bold text-white active:scale-95 transition-transform uppercase tracking-widest">Login</button>
                        </div>
                    </div>
                );
            }

            return (
                <div className="flex flex-col h-screen max-w-md mx-auto relative bg-[#020617]">
                    
                    <header className="p-4 glass z-20 flex items-center justify-between shadow-md">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-red-600 rounded-xl flex items-center justify-center">
                                <i className="fas fa-shield-halved text-white text-lg"></i>
                            </div>
                            <div><h1 className="font-bold text-lg text-white leading-none">GramRakshak</h1><p className="text-[9px] text-green-400 font-bold uppercase tracking-widest mt-1">Active | TEAM SBL</p></div>
                        </div>
                    </header>

                    <main className="flex-1 overflow-y-auto px-5 pt-6 pb-36">
                        {tab === 'home' && (
                            <div className="flex flex-col items-center">
                                <button onClick={()=>fire_sos_alert('EMERGENCY SOS')} className="w-48 h-48 rounded-full sos-btn sos-anim flex flex-col items-center justify-center border-[6px] border-slate-900 mb-8 mt-2 active:scale-90 transition-all">
                                    <i className="fas fa-tower-broadcast text-5xl mb-2 text-white"></i><span className="text-4xl font-black text-white">SOS</span>
                                </button>
                                
                                <div className="grid grid-cols-2 gap-4 w-full mb-6">
                                    <div onClick={()=>fire_sos_alert('MEDICAL')} className="glass p-4 rounded-2xl flex items-center gap-3 cursor-pointer hover-anim"><div className="bg-blue-500/20 w-10 h-10 rounded-full flex items-center justify-center"><i className="fas fa-ambulance text-blue-400 text-lg"></i></div><span className="font-bold text-sm text-white">Medical</span></div>
                                    <div onClick={()=>fire_sos_alert('FIRE')} className="glass p-4 rounded-2xl flex items-center gap-3 cursor-pointer hover-anim"><div className="bg-orange-500/20 w-10 h-10 rounded-full flex items-center justify-center"><i className="fas fa-fire text-orange-400 text-lg"></i></div><span className="font-bold text-sm text-white">Fire</span></div>
                                    <div onClick={()=>fire_sos_alert('POLICE')} className="glass p-4 rounded-2xl flex items-center gap-3 cursor-pointer hover-anim"><div className="bg-indigo-500/20 w-10 h-10 rounded-full flex items-center justify-center"><i className="fas fa-user-shield text-indigo-400 text-lg"></i></div><span className="font-bold text-sm text-white">Police</span></div>
                                    <div onClick={()=>fire_sos_alert('WOMEN_SAFETY')} className="glass p-4 rounded-2xl flex items-center gap-3 cursor-pointer hover-anim border-pink-500/30"><div className="bg-pink-500/20 w-10 h-10 rounded-full flex items-center justify-center"><i className="fas fa-person-dress text-pink-400 text-lg"></i></div><span className="font-bold text-sm text-pink-400">Women</span></div>
                                </div>
                                <div className="w-full glass p-4 rounded-2xl flex items-center gap-4"><i className={`fas fa-location-dot text-2xl ${loc.lat ? 'text-green-400' : 'text-slate-500 animate-pulse'}`}></i><div><p className="text-[10px] text-slate-400 font-bold uppercase">GPS Location</p><p className="font-bold mt-1 text-sm text-white">{loc.lat ? `${loc.lat.toFixed(5)}, ${loc.lng.toFixed(5)}` : 'Waiting for Alert...'}</p></div></div>
                            </div>
                        )}

                        {tab === 'ai' && (
                            <div className="h-full flex flex-col">
                                <div className="flex items-center gap-2 mb-4"><h2 className="text-xl font-bold text-white">AI Bot System</h2></div>
                                <div className="flex-1 glass rounded-3xl p-4 overflow-y-auto mb-4 flex flex-col gap-4">
                                    {chatBox.map((msgItem, index) => (
                                        <div key={index} className={`flex ${msgItem.sender==='user' ? 'justify-end' : 'justify-start'}`}>
                                            <div className={`max-w-[85%] p-4 text-sm font-medium ${msgItem.sender==='user' ? 'bg-red-600 text-white rounded-3xl rounded-br-none shadow-md' : 'bg-slate-800 border border-slate-700 text-slate-200 rounded-3xl rounded-bl-none'}`}>
                                                {msgItem.sender==='ai' && <i className="fas fa-robot text-blue-400 mr-2 mb-1 block text-lg"></i>}
                                                <span dangerouslySetInnerHTML={{__html: msgItem.text.replace(/\\n/g, '<br/>')}}></span>
                                            </div>
                                        </div>
                                    ))}
                                    {aiLoading && <div className="flex justify-start"><div className="bg-slate-800 border border-slate-700 rounded-3xl rounded-bl-none p-5 flex items-center justify-center"><div className="dot-flashing ml-3"></div></div></div>}
                                    <div ref={scrollRef} />
                                </div>
                                <div className="flex gap-2 mb-8">
                                    <input value={msgInput} onChange={e=>setMsgInput(e.target.value)} onKeyPress={e=>e.key==='Enter'&&handle_ai_chat()} className="flex-1 bg-slate-800 p-4 rounded-2xl outline-none text-white border border-slate-700 focus:border-red-500" placeholder="Type here..." />
                                    <button onClick={handle_ai_chat} disabled={aiLoading} className="bg-red-600 w-14 h-14 rounded-2xl flex items-center justify-center text-white active:scale-90"><i className="fas fa-paper-plane text-lg"></i></button>
                                </div>
                            </div>
                        )}
                        
                        {tab === 'serv' && (
                            <div>
                                <h2 className="text-2xl font-bold mb-6 text-white">Services</h2>
                                <div className="grid grid-cols-2 gap-4 mb-6">
                                    <div className="glass p-5 rounded-3xl border-t-2 border-red-500 text-center"><i className="fas fa-truck-medical text-3xl text-red-500 mb-3"></i><p className="text-xs text-slate-400 font-bold uppercase">Ambulance</p><p className="text-2xl font-black text-white">108</p></div>
                                    <div className="glass p-5 rounded-3xl border-t-2 border-blue-500 text-center"><i className="fas fa-user-shield text-3xl text-blue-500 mb-3"></i><p className="text-xs text-slate-400 font-bold uppercase">Police</p><p className="text-2xl font-black text-white">100</p></div>
                                </div>
                            </div>
                        )}
                        
                        {tab === 'admin' && (
                            <div>
                                <div className="flex items-center justify-between mb-6">
                                    <h2 className="text-2xl font-bold text-white">Admin Portal</h2>
                                    {adminAuth && <button onClick={()=>{setAdminAuth(false); setAdminId(''); setAdminKey('');}} className="bg-slate-800 px-3 py-1 rounded text-xs text-red-400 border border-slate-700">Logout</button>}
                                </div>
                                
                                {!adminAuth ? (
                                    <div className="glass p-6 rounded-3xl border border-slate-800">
                                        <div className="text-center mb-6">
                                            <i className="fas fa-user-lock text-4xl text-slate-500 mb-2"></i>
                                            <p className="text-sm text-slate-400 font-bold">Secure Login Required</p>
                                        </div>
                                        <input type="text" value={adminId} onChange={e=>setAdminId(e.target.value)} className="w-full bg-slate-900 border border-slate-700 p-4 rounded-xl mb-4 text-white text-sm" placeholder="Username" />
                                        <input type="password" value={adminKey} onChange={e=>setAdminKey(e.target.value)} className="w-full bg-slate-900 border border-slate-700 p-4 rounded-xl mb-6 text-white text-sm" placeholder="Password" />
                                        <button onClick={verify_admin} className="w-full bg-blue-600 py-3 rounded-xl font-bold text-white uppercase tracking-widest active:scale-95 transition-transform">Authorize</button>
                                    </div>
                                ) : (
                                    <div>
                                        <div className="grid grid-cols-2 gap-3 mb-6">
                                            <div className="glass p-4 rounded-2xl border border-red-500/30 bg-red-900/10 text-center">
                                                <p className="text-[10px] font-bold uppercase text-red-400 tracking-widest">Total Alerts</p>
                                                <p className="text-3xl font-black text-white mt-1">{dbRecords.length}</p>
                                            </div>
                                            <div onClick={sync_admin_data} className="glass p-4 rounded-2xl border border-slate-700 flex flex-col items-center justify-center cursor-pointer active:scale-95">
                                                <i className={`fas fa-rotate text-xl text-blue-400 ${loadingRecords ? 'animate-spin' : ''}`}></i>
                                                <p className="text-[10px] font-bold uppercase text-slate-400 mt-2">Refresh List</p>
                                            </div>
                                        </div>
                                        
                                        <div className="space-y-4 pb-4">
                                            {dbRecords.length === 0 && !loadingRecords && <p className="text-center text-slate-500 text-sm mt-8">No alerts found in system.</p>}
                                            {dbRecords.map(alert => (
                                                <div key={alert.id} className="glass p-4 rounded-2xl border-l-4 border-red-500">
                                                    <div className="flex justify-between items-start mb-3">
                                                        <div>
                                                            <span className="bg-red-500/20 text-red-400 text-[10px] px-2 py-1 rounded font-bold uppercase tracking-wider">{alert.type.replace('_', ' ')}</span>
                                                            <p className="text-white font-bold mt-2 text-lg tracking-wider">
                                                                <i className="fas fa-phone-alt text-slate-500 text-sm mr-2"></i>{alert.user_id}
                                                            </p>
                                                        </div>
                                                        <span className="text-[10px] text-slate-400"><i className="far fa-clock mr-1"></i>{alert.timestamp}</span>
                                                    </div>
                                                    <div className="mt-2">
                                                        <a href={`https://www.google.com/maps?q=${alert.lat},${alert.lng}`} target="_blank" className="w-full block bg-slate-800 hover:bg-slate-700 text-center py-3 rounded-xl text-sm font-bold text-blue-400 border border-slate-700 transition-colors">
                                                            <i className="fas fa-map-marker-alt mr-2 text-red-400"></i> View Location Map
                                                        </a>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}
                    </main>

                    <div className="fixed bottom-0 left-0 w-full flex justify-center z-50 pointer-events-none">
                        <nav className="w-full max-w-md bg-[#0f172a] border-t border-slate-800 flex justify-around items-center h-20 px-4 pointer-events-auto shadow-[0_-10px_30px_rgba(0,0,0,0.5)]">
                            <div onClick={()=>setTab('home')} className={`nav-item flex flex-col items-center cursor-pointer ${tab==='home'?'active':''}`}><i className="fas fa-house text-2xl mb-1"></i><span className="text-[10px] font-bold">Home</span></div>
                            <div onClick={()=>setTab('serv')} className={`nav-item flex flex-col items-center cursor-pointer ${tab==='serv'?'active':''}`}><i className="fas fa-briefcase-medical text-2xl mb-1"></i><span className="text-[10px] font-bold">Services</span></div>
                            <div onClick={()=>setTab('ai')} className={`nav-item flex flex-col items-center cursor-pointer ${tab==='ai'?'active':''}`}><i className="fas fa-robot text-2xl mb-1"></i><span className="text-[10px] font-bold">AI Bot</span></div>
                            <div onClick={()=>setTab('admin')} className={`nav-item flex flex-col items-center cursor-pointer ${tab==='admin'?'active':''}`}><i className="fas fa-user-shield text-2xl mb-1"></i><span className="text-[10px] font-bold">Admin</span></div>
                        </nav>
                    </div>

                    {isDispatching && (
                        <div className="fixed inset-0 bg-black/90 z-[9999] flex flex-col items-center justify-center pointer-events-auto backdrop-blur-sm">
                            <div className="w-16 h-16 border-4 border-red-600 border-t-transparent rounded-full animate-spin mb-4"></div>
                            <p className="text-red-500 font-bold tracking-widest animate-pulse">DISPATCHING SYSTEM ALERT...</p>
                        </div>
                    )}
                </div>
            );
        }
        const root_node = ReactDOM.createRoot(document.getElementById('root'));
        root_node.render(<GramRakshakApp />);
    </script>
</body>
</html>"""

@app.route('/')
def load_ui():
    return UI_TEMPLATE

if __name__ == '__main__':
    app.run(debug=False)
