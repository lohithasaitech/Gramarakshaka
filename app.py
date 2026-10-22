import os
import sqlite3
import requests
import base64
import threading
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

base_dir = os.path.dirname(os.path.abspath(__file__))
kalyan_db_path = os.path.join(base_dir, 'pranarakshak.db')

bot_token = "8510093946:AAEhIhVVQDDt1NNQSKAK39euzmbRdLSRtQE"
admin_chat_ids = ["6722230049", "6513585290"]

def init_kalyan_db():
    try:
        conn = sqlite3.connect(kalyan_db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS alerts 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, lat REAL, lng REAL, 
                     timestamp TEXT, status TEXT, user_id TEXT, image_front TEXT)''')
        conn.commit()
        conn.close()
    except Exception as e:
        pass

init_kalyan_db()

def dispatch_alert_by_kalyan(sos_type, lat, lng, victim, img_front, img_back):
    maps_link = f"https://www.google.com/maps?q={lat},{lng}"
    clean_type = sos_type.replace("_", " ") 
    
    alert_msg = f"🚨 <b>PRANARAKSHAK EMERGENCY</b> 🚨\n\n🆘 <b>Type:</b> {clean_type}\n👤 <b>Victim:</b> {victim}\n⏰ <b>Time:</b> {datetime.now().strftime('%I:%M %p')}\n📍 <b>Location:</b> <a href='{maps_link}'>Click to Open Map</a>\n\n<i>~ System Dispatched by TEAM SBL</i>"
    
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
                back_caption = "📸 <b>Back Camera View</b>"
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
        c.execute("INSERT INTO alerts (type, lat, lng, timestamp, status, user_id, image_front) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                  (sos_type, lat, lng, timestamp, "ACTIVE", user, img_front))
        conn.commit()
        conn.close()
    except Exception as e:
        pass
    
    bg_task = threading.Thread(target=dispatch_alert_by_kalyan, args=(sos_type, lat, lng, user, img_front, img_back))
    bg_task.start()
    
    return jsonify({"status": "success", "msg": "alert_dispatched"})

@app.route('/api/alerts', methods=['GET'])
def get_kalyan_system_alerts():
    try:
        conn = sqlite3.connect(kalyan_db_path)
        c = conn.cursor()
        c.execute("SELECT id, type, lat, lng, timestamp, status, user_id, image_front FROM alerts ORDER BY id DESC LIMIT 50")
        records = c.fetchall()
        conn.close()
        
        response_data = []
        for row in records:
            response_data.append({
                "id": row[0], "type": row[1], "lat": row[2], "lng": row[3],
                "timestamp": row[4], "status": row[5], "user_id": row[6],
                "image_front": row[7]
            })
        return jsonify({"status": "success", "data": response_data})
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)})

@app.route('/')
def serve_ui():
    return UI_TEMPLATE

UI_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>PranaRakshak - Smart Emergency Grid</title>
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
        ::-webkit-scrollbar { display: none; }
        @keyframes pulse-red { 0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); } 70% { box-shadow: 0 0 0 25px rgba(239, 68, 68, 0); } 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); } }
        .sos-anim { animation: pulse-red 2s infinite; }
        .nav-btn.active { color: #ef4444; }
    </style>
</head>
<body>
    <div id="root"></div>
    <script type="text/babel">
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
        const gemini_token = "AIzaSyCqpvRVGv5ZhmOpC2w7AOo1oHnyJrE-F9o"; 

        function GramRakshakApp() {
            const [user, setUser] = useState(null);
            const [tab, setTab] = useState('home');
            
            const [chatBox, setChatBox] = useState([{ sender: 'ai', text: "Namaste! PranaRakshak AI ni. Meeku emaina emergency help kavalante adagandi." }]);
            const [msgInput, setMsgInput] = useState('');
            
            const [contacts, setContacts] = useState([]);
            const [contactName, setContactName] = useState('');
            const [contactPhone, setContactPhone] = useState('');
            const [contactAddress, setContactAddress] = useState('');

            const [adminAuth, setAdminAuth] = useState(false);
            const [adminId, setAdminId] = useState('');
            const [adminKey, setAdminKey] = useState('');
            const [dbRecords, setDbRecords] = useState([]);

            const scrollRef = useRef(null);

            useEffect(() => {
                const savedContacts = JSON.parse(localStorage.getItem('prana_contacts') || '[]');
                setContacts(savedContacts);
            }, []);

            useEffect(() => { scrollRef.current?.scrollIntoView({ behavior: "smooth" }); }, [chatBox]);
            useEffect(() => { if(tab === 'admin' && adminAuth) sync_admin_data(); }, [tab, adminAuth]);

            const authenticate_user = () => {
                const phone_val = document.getElementById('phone_input').value;
                if (!phone_val || phone_val.length < 10) { alert("Please enter a valid phone number"); return; }
                setUser(phone_val); 
            };

            const triggerOfflineSMS = (lat, lng, type) => {
                const nums = contacts.map(c => c.phone).join(',');
                const gmap = `https://www.google.com/maps?q=${lat},${lng}`;
                const msg = `🚨 EMERGENCY ALERT (${type}) 🚨 Need help! Location: ${gmap}`;
                window.location.href = `sms:${nums}?body=${encodeURIComponent(msg)}`;
            };

            const fire_sos_alert = async (emergency_type) => {
                let currentLat = null, currentLng = null;
                let photoFront = null, photoBack = null;

                try {
                    const pos = await KalyanDeviceHelper.fetchGPS();
                    currentLat = pos.lat; currentLng = pos.lng;
                } catch(err) {
                    alert("Location Block aindi. Please enable GPS.");
                    return; 
                }

                const siren = new Audio('https://www.myinstants.com/media/sounds/police-siren.mp3');
                siren.loop = true;
                siren.play().catch(()=>{});
                
                if (emergency_type === 'EMERGENCY SOS' || emergency_type === 'MEDICAL') {
                    try { photoFront = await KalyanDeviceHelper.captureMedia('user'); } catch(e) {}
                    await new Promise(r => setTimeout(r, 400));
                    try { photoBack = await KalyanDeviceHelper.captureMedia('environment'); } catch(e) {}
                }

                if (!navigator.onLine) {
                    alert("No Internet! Sending Offline SMS to your Contacts...");
                    triggerOfflineSMS(currentLat, currentLng, emergency_type);
                    setTimeout(() => siren.pause(), 5000);
                    return;
                }

                try {
                    const res = await fetch('/api/sos', { 
                        method: 'POST', headers: {'Content-Type': 'application/json'}, 
                        body: JSON.stringify({ 
                            lat: currentLat, lng: currentLng, type: emergency_type, 
                            user: user, image_front: photoFront, image_back: photoBack 
                        }) 
                    });
                    if(res.ok){
                        alert(`✅ ${emergency_type} Alert Dispatched!`);
                    }
                } catch(e) {
                    alert("Network Failed! Sending Offline SMS...");
                    triggerOfflineSMS(currentLat, currentLng, emergency_type);
                }
                setTimeout(() => siren.pause(), 4000);
            };

            const speakAiText = (text) => {
                if ('speechSynthesis' in window) {
                    window.speechSynthesis.cancel();
                    const utterance = new SpeechSynthesisUtterance(text);
                    window.speechSynthesis.speak(utterance);
                }
            };

            const startVoiceInput = () => {
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                if (!SpeechRecognition) { alert("Voice input not supported in this browser."); return; }
                const recognition = new SpeechRecognition();
                recognition.lang = 'en-IN';
                recognition.onstart = () => alert("🎤 Listening... Speak now!");
                recognition.onresult = (e) => {
                    const transcript = e.results[0][0].transcript;
                    setMsgInput(transcript);
                };
                recognition.start();
            };

            const handle_ai_chat = async () => {
                if(!msgInput) return;
                const user_text = msgInput;
                setChatBox(p => [...p, { sender: 'user', text: user_text }]);
                setMsgInput('');
                
                const sys_prompt = `Act as an emergency medical and safety assistant. STRICT RULE: You MUST detect the language of the user's question and reply in the EXACT SAME LANGUAGE and SCRIPT. If user types in pure Telugu script, reply ONLY in pure Telugu script. If user types in English, reply in English. If user types Telugu in English alphabet (Tanglish), reply in Tanglish. Keep reply under 3 short sentences. User question: ${user_text}`;

                try {
                    const res = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${gemini_token}`, {
                        method: 'POST', headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ contents: [{ parts: [{ text: sys_prompt }] }] })
                    });
                    const ai_data = await res.json();
                    const final_reply = ai_data.candidates[0].content.parts[0].text;
                    setChatBox(p => [...p, { sender: 'ai', text: final_reply }]);
                    speakAiText(final_reply);
                } catch (e) {
                    setChatBox(p => [...p, { sender: 'ai', text: "Error. Try again." }]);
                }
            };

            const saveContact = () => {
                if(!contactName || !contactPhone) return;
                const newContacts = [...contacts, {name: contactName, phone: contactPhone, address: contactAddress}];
                setContacts(newContacts);
                localStorage.setItem('prana_contacts', JSON.stringify(newContacts));
                setContactName(''); setContactPhone(''); setContactAddress('');
                alert("Contact Saved!");
            };

            const deleteContact = (index) => {
                const updated = contacts.filter((_, i) => i !== index);
                setContacts(updated);
                localStorage.setItem('prana_contacts', JSON.stringify(updated));
            };

            const verify_admin = () => {
                if(adminId === 'admin' && adminKey === 'Lohitha@123') setAdminAuth(true);
                else alert("Invalid Credentials!");
            };

            const sync_admin_data = async () => {
                try {
                    const res = await fetch('/api/alerts');
                    const data = await res.json();
                    if(data.status === 'success') setDbRecords(data.data);
                } catch(e) {}
            };

            if(!user) {
                return (
                    <div className="h-screen flex flex-col items-center justify-center p-6 bg-slate-950">
                        <div className="w-24 h-24 bg-red-600 rounded-3xl flex items-center justify-center mb-6 shadow-[0_0_30px_rgba(239,68,68,0.5)]">
                            <i className="fas fa-heartbeat text-5xl text-white"></i>
                        </div>
                        <h1 className="text-4xl font-black mb-2 tracking-tighter text-white">PRANARAKSHAK</h1>
                        <p className="mb-10 text-slate-400 text-xs font-bold text-center uppercase tracking-widest">Smart Emergency Grid<br/><span className="text-red-500 mt-1 inline-block">DEVELOPED BY TEAM SBL</span></p>
                        <div className="glass w-full p-8 rounded-[2rem]">
                            <label className="text-[10px] text-slate-400 font-black uppercase mb-2 block">Mobile / ID</label>
                            <input id="phone_input" type="number" className="w-full bg-slate-800 p-4 rounded-xl mb-6 outline-none text-white font-bold" placeholder="Enter Your Number" />
                            <button onClick={authenticate_user} className="w-full bg-red-600 py-4 rounded-xl font-bold text-white active:scale-95 transition-transform uppercase tracking-widest">Activate Shield</button>
                        </div>
                    </div>
                );
            }

            return (
                <div className="flex flex-col h-screen max-w-md mx-auto relative bg-[#020617]">
                    
                    <header className="p-4 glass z-20 flex items-center justify-between shadow-md">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-red-600 rounded-xl flex items-center justify-center">
                                <i className="fas fa-heartbeat text-white text-lg"></i>
                            </div>
                            <div>
                                <h1 className="font-bold text-lg text-white leading-none">PranaRakshak</h1>
                                <p className="text-[9px] text-green-400 font-bold uppercase tracking-widest mt-1">Active Grid | SBL</p>
                            </div>
                        </div>
                    </header>

                    <main className="flex-1 overflow-y-auto px-5 pt-6 pb-24">
                        
                        {tab === 'home' && (
                            <div className="flex flex-col items-center">
                                <button onClick={()=>fire_sos_alert('EMERGENCY SOS')} className="w-48 h-48 rounded-full sos-btn sos-anim flex flex-col items-center justify-center border-[6px] border-slate-900 mb-8 mt-4 active:scale-90 transition-all">
                                    <i className="fas fa-tower-broadcast text-5xl mb-2 text-white"></i>
                                    <span className="text-4xl font-black text-white">SOS</span>
                                </button>
                                
                                <div className="grid grid-cols-2 gap-4 w-full mb-6">
                                    <div onClick={()=>fire_sos_alert('MEDICAL')} className="glass p-4 rounded-2xl flex flex-col items-center gap-2 cursor-pointer active:scale-95 transition-transform">
                                        <div className="bg-blue-500/20 w-12 h-12 rounded-full flex items-center justify-center"><i className="fas fa-ambulance text-blue-400 text-xl"></i></div>
                                        <span className="font-bold text-sm text-white">Medical</span>
                                    </div>
                                    <div onClick={()=>fire_sos_alert('FIRE')} className="glass p-4 rounded-2xl flex flex-col items-center gap-2 cursor-pointer active:scale-95 transition-transform">
                                        <div className="bg-orange-500/20 w-12 h-12 rounded-full flex items-center justify-center"><i className="fas fa-fire text-orange-400 text-xl"></i></div>
                                        <span className="font-bold text-sm text-white">Fire</span>
                                    </div>
                                </div>
                            </div>
                        )}

                        {tab === 'contacts' && (
                            <div className="flex flex-col">
                                <h2 className="text-xl font-bold mb-4 text-white"><i className="fas fa-users mr-2 text-blue-400"></i>Emergency Contacts</h2>
                                <div className="glass p-4 rounded-2xl mb-6">
                                    <input value={contactName} onChange={e=>setContactName(e.target.value)} placeholder="Relative Name" className="w-full bg-slate-800 p-3 rounded-lg mb-3 outline-none text-white text-sm" />
                                    <input value={contactPhone} onChange={e=>setContactPhone(e.target.value)} type="number" placeholder="Phone Number" className="w-full bg-slate-800 p-3 rounded-lg mb-3 outline-none text-white text-sm" />
                                    <input value={contactAddress} onChange={e=>setContactAddress(e.target.value)} placeholder="Address / Location" className="w-full bg-slate-800 p-3 rounded-lg mb-4 outline-none text-white text-sm" />
                                    <button onClick={saveContact} className="w-full bg-blue-600 py-3 rounded-lg font-bold text-white text-sm">Save Contact</button>
                                </div>

                                <div className="space-y-3">
                                    {contacts.map((c, i) => (
                                        <div key={i} className="glass p-4 rounded-xl flex justify-between items-center">
                                            <div>
                                                <h3 className="font-bold text-white">{c.name}</h3>
                                                <p className="text-xs text-slate-400">{c.phone}</p>
                                                <p className="text-xs text-slate-500">{c.address}</p>
                                            </div>
                                            <button onClick={()=>deleteContact(i)} className="text-red-500"><i className="fas fa-trash"></i></button>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {tab === 'chat' && (
                            <div className="flex flex-col h-full">
                                <div className="flex-1 overflow-y-auto space-y-4 mb-4">
                                    {chatBox.map((msg, idx) => (
                                        <div key={idx} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                                            <div className={`p-3 max-w-[80%] rounded-2xl text-sm ${msg.sender === 'user' ? 'bg-red-600 text-white rounded-br-none' : 'glass text-slate-200 rounded-bl-none'}`}>
                                                {msg.text}
                                            </div>
                                        </div>
                                    ))}
                                    <div ref={scrollRef}></div>
                                </div>
                                <div className="flex gap-2">
                                    <button onClick={startVoiceInput} className="bg-slate-800 w-12 h-12 rounded-xl flex items-center justify-center text-white active:scale-95"><i className="fas fa-microphone"></i></button>
                                    <input value={msgInput} onChange={e=>setMsgInput(e.target.value)} placeholder="Ask anything..." className="flex-1 bg-slate-800 rounded-xl px-4 outline-none text-white" />
                                    <button onClick={handle_ai_chat} className="bg-red-600 w-12 h-12 rounded-xl flex items-center justify-center text-white active:scale-95"><i className="fas fa-paper-plane"></i></button>
                                </div>
                            </div>
                        )}

                        {tab === 'admin' && (
                            <div className="flex flex-col">
                                {!adminAuth ? (
                                    <div className="glass p-6 rounded-2xl mt-10">
                                        <h2 className="text-xl font-bold mb-4 text-center">Admin Login</h2>
                                        <input value={adminId} onChange={e=>setAdminId(e.target.value)} placeholder="User ID" className="w-full bg-slate-800 p-3 rounded-lg mb-3 outline-none text-white text-sm" />
                                        <input value={adminKey} onChange={e=>setAdminKey(e.target.value)} type="password" placeholder="Password" className="w-full bg-slate-800 p-3 rounded-lg mb-4 outline-none text-white text-sm" />
                                        <button onClick={verify_admin} className="w-full bg-red-600 py-3 rounded-lg font-bold text-white text-sm">Login</button>
                                    </div>
                                ) : (
                                    <div className="space-y-4">
                                        <div className="flex justify-between items-center mb-4">
                                            <h2 className="text-xl font-bold text-white">Alert Grid</h2>
                                            <button onClick={sync_admin_data} className="bg-slate-800 px-3 py-1 rounded-lg text-xs"><i className="fas fa-sync mr-1"></i>Refresh</button>
                                        </div>
                                        {dbRecords.map((r, i) => (
                                            <div key={i} className="glass p-4 rounded-xl border-l-4 border-l-red-500">
                                                <div className="flex justify-between items-start mb-2">
                                                    <span className="bg-red-500/20 text-red-400 text-xs font-bold px-2 py-1 rounded">{r.type}</span>
                                                    <span className="text-[10px] text-slate-400">{r.timestamp}</span>
                                                </div>
                                                <p className="text-sm text-slate-300 mb-1"><i className="fas fa-user mr-2"></i>{r.user_id}</p>
                                                <a href={`https://www.google.com/maps?q=${r.lat},${r.lng}`} target="_blank" className="text-xs text-blue-400 underline mb-3 block"><i className="fas fa-location-dot mr-1"></i>View on Map</a>
                                                {r.image_front && (
                                                    <img src={r.image_front} className="w-full h-32 object-cover rounded-lg border border-slate-700 mt-2" alt="Victim Face" />
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        )}

                    </main>

                    <nav className="absolute bottom-0 w-full glass p-4 flex justify-between items-center z-20 rounded-t-3xl border-b-0 pb-6">
                        <button onClick={()=>setTab('home')} className={`nav-btn flex flex-col items-center gap-1 ${tab==='home'?'active':'text-slate-500'}`}>
                            <i className="fas fa-house text-xl"></i><span className="text-[10px] font-bold">Home</span>
                        </button>
                        <button onClick={()=>setTab('contacts')} className={`nav-btn flex flex-col items-center gap-1 ${tab==='contacts'?'active':'text-slate-500'}`}>
                            <i className="fas fa-address-book text-xl"></i><span className="text-[10px] font-bold">Contacts</span>
                        </button>
                        <button onClick={()=>setTab('chat')} className={`nav-btn flex flex-col items-center gap-1 ${tab==='chat'?'active':'text-slate-500'}`}>
                            <i className="fas fa-robot text-xl"></i><span className="text-[10px] font-bold">AI Chat</span>
                        </button>
                        <button onClick={()=>setTab('admin')} className={`nav-btn flex flex-col items-center gap-1 ${tab==='admin'?'active':'text-slate-500'}`}>
                            <i className="fas fa-shield text-xl"></i><span className="text-[10px] font-bold">Admin</span>
                        </button>
                    </nav>
                </div>
            );
        }

        const root = ReactDOM.createRoot(document.getElementById('root'));
        root.render(<GramRakshakApp />);
    </script>
</body>
</html>"""

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
