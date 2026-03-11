# ZeroRange — YouTube Video EP1 Content

## SECTION 1 — IDEA

Introduction of ZeroRange, a gamified physical security training platform for the Flipper Zero built on a Raspberry Pi 5. The viewer discovers the concept (iButton, NFC, RFID, SubGHz, IR challenges with scoring), the hardware used, a live demo of the system running with the LCD screen, and the open source architecture. First video in a series — the goal is to show the project as-is, explain the vision, and invite the community to contribute or use it as a base for CTFs, escape games, or training platforms.

---

## SECTION 2 — TRANSCRIPT

### Chapter 1: Introduction — What is ZeroRange? (00:00)

Hey everyone, welcome back to SamXplogs.

So I've been working on something for a while now and I decided to make this video before the project becomes irrelevant — because let's be honest, in this space things move fast.

The idea is simple. If you own a Flipper Zero, you probably played with it a few times, scanned a couple of NFC cards, maybe messed around with Sub-GHz signals, and then... it sits in a drawer. Right? We've all been there.

So I asked myself: what if there was a way to actually practice and get better with it? Like a structured training environment where you have clear objectives, you score points, and you can track your progress.

That's ZeroRange. Think of it as a shooting range, but for your Flipper Zero. A hands-on training platform with real hardware challenges — iButton, NFC, RFID, Sub-GHz, Infrared — all running on a Raspberry Pi with a little LCD screen that tells you what to do.

Let me show you how it works.

---

### Chapter 2: The Concept — A Shooting Range for Flipper Zero (XX:XX)

So the concept behind ZeroRange is pretty straightforward.

You have a Raspberry Pi 5 sitting on your desk. Plugged into it you have different peripherals — an iButton USB reader, a Proxmark3 for NFC and RFID, a HackRF One for Sub-GHz signals. And on top of the Pi, there's a 16x2 LCD screen with buttons that acts as your main interface.

The system gives you challenges. 15 of them right now, organized into 5 modules: iButton, NFC, RFID, Sub-GHz, and IR. Each challenge is worth 10 points, so the max score is 150.

The challenges are progressive. In each module, you start with something simple — like detecting a tag or capturing a signal. Then it gets harder — cloning, replaying, analyzing protocols. The idea is that you learn by doing, step by step.

Everything is gamified. You see your score on the LCD, your progress is saved in a SQLite database, and you can reset and start over whenever you want. It's basically a CTF that lives on your desk.

And the whole thing is open source. Everything is on GitHub. You can fork it, modify the challenges, add your own modules, whatever you want.

---

### Chapter 3: Hardware — Raspberry Pi 5, LCD, Peripherals (XX:XX)

Let me walk you through the hardware.

At the core, we have a Raspberry Pi 5 with 4 gigs of RAM. That's the brain of the operation. It runs the Python application, hosts the web documentation, and manages all the peripherals.

On top of the Pi, I'm using the Adafruit RGB LCD Shield — it's a 16x2 character display that communicates over I2C. It has 5 built-in buttons: up, down, left, right, and select. That's your entire interface right there. No monitor needed, no keyboard. Just the LCD and the buttons.

For iButton challenges, I have a USB iButton reader. It's a cheap module from AliExpress that acts as a HID keyboard — when you touch an iButton to the reader, it types out the ID. Simple but effective.

For NFC and RFID, I'm using a Proxmark3. This thing is the gold standard for contactless card research. It handles 13.56 MHz NFC cards — MIFARE Classic, Ultralight, NTAG — and also 125 kHz RFID tags like EM4100 and HID.

For Sub-GHz challenges, there's a HackRF One plugged in. This is a software-defined radio that covers 1 MHz to 6 GHz. We use it mainly on 433.92 MHz to capture and replay RF signals — the kind of stuff you find in garage door remotes, keyfobs, sensors.

And for IR, there's a FLIRC USB receiver, though that module is still being developed.

All the links are in the description if you want to grab any of this hardware. And yes, those are affiliate links — they help me fund the gear for these projects.

---

### Chapter 4: Software Architecture and Tech Stack (XX:XX)

Let's talk about how the software is put together, because I think it's important if you want to fork this or build on top of it.

The whole thing is written in Python 3. The main application is `zerorange.py` — it's a state machine that handles the menu navigation, the challenge flow, and all the user interactions through the LCD.

Each hardware module has its own handler. So you have `ibutton_handler.py`, `nfc_handler.py`, `rfid_handler.py`, `subghz_handler.py`, and `ir_handler.py`. These contain the challenge logic — what to display, how to validate, how to score.

Then there are the low-level hardware interfaces. `proxmark_handler.py` talks to the Proxmark3 via subprocess commands. `hackrf_handler.py` does the same with `hackrf_transfer` for signal capture and replay. Everything goes through the command line — no custom drivers needed.

The challenges themselves are defined in JSON files inside the `challenges/` folder. Each module has its own JSON file — `ibutton.json`, `nfc.json`, `rfid.json`, `subghz.json`, `ir.json`. There's even a schema file and a documentation page explaining how to create your own challenges. So if you want to add a new challenge, you just edit a JSON file and write the corresponding handler logic.

Scores and attempt history are stored in a SQLite database — `scores.db`. It tracks which challenges you completed, your best times, and how many attempts you made.

The system also runs as a systemd service, so it starts automatically when the Pi boots up. No need to SSH in and run scripts manually — just power it on and you're good to go.

---

### Chapter 5: Demo — Navigating the LCD Menus (XX:XX)

Alright, let me show you the system running.

So when the Pi boots up, the LCD shows the home screen — "ZeroRange V1" and the IP address. You press any button and you're in the main menu.

From here you can scroll through the modules with up and down — iButton, NFC, RFID, SubGHz, IR, Settings. Your current score is displayed on the right side of the screen.

Let's go into iButton. You see three challenges listed: "Ch1: Touch", "Ch2: Clone", "Ch3: Emulate". If you've already completed one, there's a little checkmark next to it. You navigate with up and down, press select to start a challenge, or left to go back.

Same thing for every module. The navigation is consistent — up, down, select, back. Simple.

In Settings you can see your stats — total score, how many challenges completed, total attempts — or reset everything to start fresh.

---

### Chapter 6: iButton Challenge — Touch & Read Live (XX:XX)

Let me run the first iButton challenge live so you can see how it works.

I select "Ch1: Touch" and press select. The LCD shows "Touch iButton" with a 60-second countdown. Now I just need to take an iButton — this little metal key — and touch it to the USB reader.

And there it is — the system detected the iButton, it reads the ID, and displays it on screen. "SOLVED! +10 points." Just like that.

The second challenge is cloning — the system reads one iButton, remembers the ID, then asks you to present a second one and checks if you can emulate the first one's ID on it.

The third challenge gives you a specific target ID and you need to program your Flipper to emulate exactly that ID. It's checking for an exact match.

These are simple challenges but they teach you the fundamentals of 1-Wire protocol — reading, cloning, emulation. The same workflow you'd use in a real-world physical security assessment.

---

### Chapter 7: NFC / RFID Challenge with the Proxmark3 (XX:XX)

Now let's look at the NFC and RFID modules. These require the Proxmark3 to be plugged in.

For NFC, challenge 4 is "Detect & Read" — you place any NFC card on the Proxmark3 antenna and the system reads the UID and card type. It supports MIFARE Classic, Ultralight, NTAG, and other ISO14443A cards.

Challenge 5 is cloning — you read a card, then the system asks you to write that UID to a magic card, a Gen1a or Gen2 writable card. It verifies the clone was successful.

Challenge 6 is the most advanced — a MIFARE Classic nested key recovery attack. The Proxmark3 runs the actual attack, recovers the encryption keys, and dumps the card sectors. This is real pentest stuff.

On the RFID side, it's similar but for 125 kHz tags. Detect an EM4100 tag, clone it to a T5577 writable card, or simulate an EM410x tag with your Flipper Zero. The Proxmark3 acts as the verifier on this side.

If the Proxmark3 isn't plugged in, the menu just shows "NFC - No PM3" and you can go back. No crash, no error — it gracefully handles missing hardware.

---

### Chapter 8: SubGHz Challenge with the HackRF One (XX:XX)

The SubGHz module is where things get really interesting. This requires a HackRF One.

Challenge 10 is signal detection. The HackRF listens on 433.92 MHz — the most common frequency for garage door remotes, keyfobs, and wireless sensors in Europe. You take any device that transmits on that frequency, press the button near the HackRF antenna, and the system captures the signal. It measures the signal strength in dBm and needs it above minus 55 to validate.

Challenge 11 is record and replay. The HackRF records whatever signal you transmit, saves the raw capture, and then replays it back three times automatically. This demonstrates the classic replay attack — and also shows you why modern systems use rolling codes.

Challenge 12 is signal analysis. You send a signal, the HackRF captures it, and the system tries to identify the protocol and modulation type. It can detect OOK modulation and common protocols like Princeton, CAME, and Nice FLO. If you have rtl_433 installed, it uses that for deeper analysis.

For this module, the key thing is getting close enough to the HackRF antenna. The detection threshold is set to minus 55 dBm, so you typically need to be within a meter or so. If it doesn't detect anything, check your frequency and get closer.

---

### Chapter 9: Web Interface and Documentation (XX:XX)

ZeroRange also comes with a built-in web interface. The Pi runs two web servers.

On port 8000, there's an HTTP server that hosts the documentation — a full HTML documentation page with all the project info, hardware setup guides, challenge descriptions, and troubleshooting.

On port 5000, there's a Flask API that mirrors the LCD state. You can see what's on the LCD screen from your browser and even send button presses remotely. It's basically a web-based LCD simulator. Pretty useful when you don't have physical access to the Pi or when you're demonstrating remotely.

To access it, just open a browser and go to the Pi's IP address on port 8000. If you're connected to the same network, it just works. The Pi can also run as a WiFi hotspot called "ZeroRange" — so you don't even need an existing network. Just connect to the hotspot and access the docs.

---

### Chapter 10: Use Cases — CTF, Escape Game, Training (XX:XX)

Now here's where I think this project has real potential beyond my desk.

First — CTF competitions. Physical security challenges are often the weakest part of CTFs because they're hard to set up. ZeroRange gives you a ready-made platform. Drop a Pi at each station, plug in the relevant hardware, and you have a scored physical hacking challenge.

Second — escape games. Imagine an escape room where one of the puzzles is cloning an NFC badge or replaying an RF signal to "unlock a door." ZeroRange provides the scoring and validation engine, you just need to build the scenario around it.

Third — training and education. If you're teaching a cybersecurity class or running a hackerspace workshop, this gives students a structured, hands-on way to learn. They can practice at their own pace, track their progress, and you can see who completed what.

Fourth — personal practice. That's my original use case. I wanted to get better with my Flipper Zero, and having structured challenges with scoring keeps me motivated way more than just randomly scanning things.

The challenges are defined in JSON files, so you can customize everything — change the difficulty, adjust timeouts, add new modules. The format is documented in the repo if you want to create your own scenarios.

---

### Chapter 11: The Project is Open Source — Contribute! (XX:XX)

Everything is on GitHub at github.com/samxplogs/ZeroRange. MIT-compatible license, so you can use it however you want.

I want to be honest with you — this project is not perfect. There's still work to do, especially on the challenge scenarios. The IR module is still in development, some edge cases aren't handled perfectly, and the web interface could use some love.

But that's kind of the point of this channel. I like to explore and give you a kick to do the same. I'm pretty sure people have already worked on similar projects — door simulators, badge cloners, RF training rigs. So I'd love to hear what you've built or what you think could be improved.

If you want to contribute, here are some ideas: write new challenges, add support for new protocols, improve the web interface, or even build a physical enclosure for the whole thing. Open an issue, submit a PR, or just fork it and make it your own.

---

### Chapter 12: What's Left to Do and Next Steps (XX:XX)

Let me be transparent about where the project stands and what's coming next.

Right now, the core system works — the state machine, the LCD interface, the scoring, the iButton module, NFC, RFID, and SubGHz modules are all functional. The IR module exists but the FLIRC integration still needs work.

On my roadmap, here's what I want to tackle:

The challenge scenarios need more depth. Right now they're fairly straightforward — detect, clone, replay. I want to add more creative scenarios, maybe multi-step challenges that span across modules, or timed challenges where speed matters.

The web interface needs to be synced with the actual application state. Right now the web LCD server and the main app are somewhat independent — I want them to talk to each other in real time.

I also want to add multi-player support. Imagine two people competing side by side, each with their own setup, racing to complete the same challenges.

And eventually, I'd love to see community-contributed challenge packs — like downloadable JSON files that add themed scenarios. A "hotel pentest" pack, a "smart home" pack, a "vehicle security" pack. That's the long-term vision.

For now though, what you see is what you get. And I think it's already a solid foundation to build on.

---

### Chapter 13: Conclusion and Useful Links (XX:XX)

Alright, that's ZeroRange. A Raspberry Pi-based shooting range for your Flipper Zero. 15 challenges, 5 modules, fully open source.

If you want to build your own, all the links are in the description — the GitHub repo, the hardware with affiliate links, and the documentation.

If you've built something similar or have ideas for new challenges, drop a comment. I'm genuinely curious to see what the community comes up with.

If you enjoyed this video, smash that like button and subscribe for more hardware hacking content. And if you want to support the channel, there's a Ko-fi link in the description — every coffee helps keep this lab running.

Thanks for watching. I'll see you in the next one.

---

## SECTION 3 — TITLES (x3)

1. **I Built a Shooting Range for Flipper Zero with a Raspberry Pi**
2. **ZeroRange: Flipper Zero Training Platform (Open Source)**
3. **12 Physical Hacking Challenges on Raspberry Pi — ZeroRange**

---

## SECTION 4 — THUMBNAIL IDEAS (x3)

1. **Thumbnail 1 (for title 1):** Close-up of the Flipper Zero sitting next to the Raspberry Pi with the LCD screen lit up showing the ZeroRange menu. Bold text overlay: "SHOOTING RANGE" in yellow/orange on a dark background. A target/crosshair visual in the background. Dominant colors: black, orange, green (Flipper LED).

2. **Thumbnail 2 (for title 2):** Split screen: left side shows the full setup (Pi + LCD + cables), right side shows the LCD screen with the score. Text overlay: "OPEN SOURCE" in neon green + GitHub logo. A "v1.0" badge in a corner. Dominant colors: purple/blue gradient (cybersec style), neon green.

3. **Thumbnail 3 (for title 3):** Top-down view of the complete setup with all peripherals plugged in (Proxmark3, HackRF, iButton reader). Text overlay: "12 CHALLENGES" with RF/NFC/RFID icons around it. Arrow pointing at the LCD screen. Dominant colors: matte black, red, white.

---

## SECTION 5 — YOUTUBE DESCRIPTION

### Summary

I built ZeroRange, an open source training platform for the Flipper Zero based on a Raspberry Pi 5. The system features 15 gamified challenges covering iButton, NFC, RFID, SubGHz, and Infrared, with a 16x2 LCD screen as the interface and a persistent scoring system. In this first video, I walk you through the concept, the hardware, a live demo, and how it could serve as a foundation for CTFs, escape games, or physical security training.

---

### Resources & Links

- 🔗 ZeroRange GitHub: https://github.com/samxplogs/ZeroRange
- 🔗 Project web documentation: accessible at `http://[PI_IP]:8000/documentation.html`
- 📄 Full installation guide: https://github.com/samxplogs/ZeroRange/blob/main/INSTALLATION.md
- 📄 Proxmark3 integration: https://github.com/samxplogs/ZeroRange/blob/main/PROXMARK_INTEGRATION.md
- 📄 HackRF/SubGHz integration: https://github.com/samxplogs/ZeroRange/blob/main/SUBGHZ_INTEGRATION.md
- 📄 Challenge format (JSON): https://github.com/samxplogs/ZeroRange/blob/main/docs/CHALLENGE_FORMAT.md

---

### Hardware Used (affiliate links*)

- 🔧 Raspberry Pi 5 (4GB): https://amzn.to/3O4jeX1
- 🔧 Adafruit i2c 16x2 RGB LCD Shield: https://amzn.to/4rGhYrK
- 🔧 Proxmark3 (Amazon): https://amzn.to/4akFmDZ
- 🔧 Proxmark3 (AliExpress): https://s.click.aliexpress.com/e/_c3znHpUL
- 🔧 HackRF One (Amazon): https://amzn.to/4ttmuvs
- 🔧 HackRF + PortaPack (AliExpress): https://s.click.aliexpress.com/e/_c3vH9LoF
- 🔧 iButton USB Reader (AliExpress): https://s.click.aliexpress.com/e/_c3KQ9ToL
- *Affiliate links help me fund the gear and subscriptions needed to create these videos. Thanks for your support!

---

### Chapters

- 00:00 — Introduction: What is ZeroRange?
- XX:XX — The concept: a shooting range for Flipper Zero
- XX:XX — Hardware: Raspberry Pi 5, LCD, peripherals
- XX:XX — Software architecture and tech stack
- XX:XX — Demo: navigating the LCD menus
- XX:XX — iButton challenge: Touch & Read live
- XX:XX — NFC / RFID challenge with the Proxmark3
- XX:XX — SubGHz challenge with the HackRF One
- XX:XX — Web interface and documentation
- XX:XX — Use cases: CTF, escape game, training
- XX:XX — The project is open source — contribute!
- XX:XX — What's left to do and next steps
- XX:XX — Conclusion and useful links

---

### Support via Ko-fi

Want to buy me a drink, like an e-coffee or Club-Mate? You can do so at https://ko-fi.com/samxplogs. You'll have my infinite gratitude. Thanks a lot for helping keep the lights on in my home lab!

---

### Follow SamXplogs

🌐 YouTube: https://www.youtube.com/@samxplogs
💻 GitHub: https://github.com/samxplogs

---

## SECTION 6 — YOUTUBE TAGS

flipper zero, flipper zero training, zerorange, raspberry pi 5, physical hacking, physical security, ibutton hacking, nfc cloning, rfid cloning, proxmark3, hackrf one, subghz, sub-ghz hacking, 433mhz, signal replay, mifare classic attack, em4100, t5577, infrared hacking, cybersecurity training, CTF physical, escape game hacking, pentest hardware, open source security, raspberry pi project, LCD i2c, gamified learning, flipper zero tutorial, ethical hacking, hardware hacking

---

## SECTION 7 — SEO KEYWORDS (max 500 characters)

flipper zero training platform, how to learn flipper zero, physical CTF platform, raspberry pi security, flipper zero shooting range, clone NFC badge proxmark3, hackrf 433mhz replay, physical security challenge, flipper zero open source, escape game cybersecurity, ibutton clone flipper, open source security training, proxmark3 tutorial, hackrf signal capture replay

---

## SECTION 8 — LINKS & INFO

- **Tools/software used:** Python 3, Flask, SQLite, hackrf_transfer, rtl_433, Proxmark3 client, smbus2, systemd
- **Hardware shown:** Raspberry Pi 5, Adafruit LCD 16x2 RGB, Proxmark3, HackRF One, iButton USB Reader, Flipper Zero
- **Affiliate links available:** Amazon (Pi 5, LCD, Proxmark3, HackRF), AliExpress (Proxmark3, HackRF+PortaPack, iButton reader)
- **External resources to mention:** GitHub repo, embedded web documentation, CHALLENGE_FORMAT.md for creating custom challenges
- **Collaborations/mentions:** Call to the community to contribute, fork, and propose new scenarios

---

## CHECKLIST BEFORE PUBLISHING

- [ ] Title selected (from the 3 proposals)
- [ ] Thumbnail created (based on chosen concept)
- [ ] Full description copied
- [ ] Chapters verified with real timestamps
- [ ] Tags added
- [ ] SEO keywords added
- [ ] Affiliate links verified and working
- [ ] Ko-fi link present
- [ ] YouTube category: Science & Technology
- [ ] Language: English

---

*Template v1.0 — SamXplogs — Cybersecurity Content Creator*
