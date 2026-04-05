from __future__ import annotations

import random
import re
from dataclasses import dataclass
from typing import Any

from app.core.config import settings


@dataclass
class LetterDraft:
    subject: str
    body: str


LANGUAGE_NAME_MAP = {
    "en": "English", "hi": "Hindi", "bn": "Bengali", "ta": "Tamil",
    "te": "Telugu", "ml": "Malayalam", "mr": "Marathi", "kn": "Kannada",
    "gu": "Gujarati", "pa": "Punjabi", "ur": "Urdu",
}

# Per-language phrase banks: {lang_code: {key: [variants]}}
_PHRASES: dict[str, dict[str, list[str]]] = {
    "en": {
        "salutation": ["Dear Sir/Madam,", "Respected Authority,", "To Whom It May Concern,"],
        "intro": [
            "I am writing to formally report a civic issue that requires urgent attention.",
            "I wish to bring to your notice a matter of public concern that demands immediate action.",
            "This letter is to formally lodge a complaint regarding a municipal infrastructure issue.",
        ],
        "location_prefix": ["The issue is located at", "The problem has been observed at", "This has been reported from"],
        "action_request": [
            "I kindly request your department to inspect and resolve this at the earliest.",
            "I urge the concerned authority to take prompt corrective action.",
            "Please ensure the matter is addressed on priority.",
        ],
        "closing": ["Yours sincerely,", "Respectfully yours,", "With regards,"],
        "subject_prefix": "Complaint regarding",
        "citizen_input_label": "Additional details from the citizen",
        "recommendations_label": "Recommended corrective actions",
        "tracking_label": "Tracking ID",
        "severity_label": "Severity Score",
        "priority_label": "Priority Level",
        "location_label": "Location",
    },
    "hi": {
        "salutation": ["माननीय महोदय/महोदया,", "आदरणीय अधिकारी महोदय,", "संबंधित विभाग को,"],
        "intro": [
            "मैं आपके समक्ष एक नागरिक समस्या की औपचारिक शिकायत दर्ज करना चाहता/चाहती हूँ जिस पर तत्काल ध्यान देने की आवश्यकता है।",
            "मैं आपको एक सार्वजनिक बुनियादी ढाँचे की समस्या से अवगत कराना चाहता/चाहती हूँ जिसके लिए त्वरित कार्रवाई आवश्यक है।",
            "यह पत्र एक गंभीर नागरिक समस्या की जानकारी देने हेतु लिखा जा रहा है।",
        ],
        "location_prefix": ["यह समस्या यहाँ पाई गई है", "यह मुद्दा निम्नलिखित स्थान पर देखा गया है", "शिकायत स्थान"],
        "action_request": [
            "मेरा आपसे अनुरोध है कि इस स्थान का निरीक्षण कर अविलंब सुधारात्मक कदम उठाए जाएँ।",
            "कृपया संबंधित विभाग को इस समस्या का समाधान प्राथमिकता के आधार पर करने का निर्देश दें।",
            "मैं आपसे अनुरोध करता/करती हूँ कि इस मामले में शीघ्र कार्रवाई की जाए।",
        ],
        "closing": ["आपका विश्वासपात्र,", "सादर,", "भवदीय,"],
        "subject_prefix": "शिकायत:",
        "citizen_input_label": "नागरिक द्वारा दी गई अतिरिक्त जानकारी",
        "recommendations_label": "सुझाए गए सुधारात्मक उपाय",
        "tracking_label": "ट्रैकिंग आईडी",
        "severity_label": "गंभीरता स्कोर",
        "priority_label": "प्राथमिकता स्तर",
        "location_label": "स्थान",
    },
    "bn": {
        "salutation": ["মাননীয় মহোদয়/মহোদয়া,", "শ্রদ্ধেয় কর্তৃপক্ষ,", "সংশ্লিষ্ট বিভাগ বরাবর,"],
        "intro": [
            "আমি একটি গুরুত্বপূর্ণ নাগরিক সমস্যার আনুষ্ঠানিক অভিযোগ জানাতে এই পত্র লিখছি যা অবিলম্বে মনোযোগের দাবি রাখে।",
            "জনসাধারণের অবকাঠামো সংক্রান্ত একটি গুরুত্বপূর্ণ বিষয়ে আপনাদের দৃষ্টি আকর্ষণ করতে এই চিঠি লেখা হচ্ছে।",
            "এই পত্রের মাধ্যমে একটি পৌর সমস্যার আনুষ্ঠানিক অভিযোগ দায়ের করা হচ্ছে।",
        ],
        "location_prefix": ["সমস্যাটি এখানে দেখা গেছে", "এই সমস্যা নিচের স্থানে চিহ্নিত হয়েছে", "অভিযোগের স্থান"],
        "action_request": [
            "আমি অনুরোধ করছি যে আপনার বিভাগ অবিলম্বে এই স্থান পরিদর্শন করে প্রয়োজনীয় ব্যবস্থা নিন।",
            "দয়া করে এই সমস্যাটি অগ্রাধিকার ভিত্তিতে সমাধান করুন।",
        ],
        "closing": ["বিনীত নিবেদক,", "শ্রদ্ধাসহকারে,", "আপনার বিশ্বস্ত,"],
        "subject_prefix": "অভিযোগ:",
        "citizen_input_label": "নাগরিকের অতিরিক্ত তথ্য",
        "recommendations_label": "প্রস্তাবিত সংশোধনমূলক পদক্ষেপ",
        "tracking_label": "ট্র্যাকিং আইডি",
        "severity_label": "তীব্রতা স্কোর",
        "priority_label": "অগ্রাধিকার স্তর",
        "location_label": "অবস্থান",
    },
    "ta": {
        "salutation": ["மதிப்பிற்குரிய அம்மா/ஐயா,", "மரியாதைக்குரிய அதிகாரி,", "சம்பந்தப்பட்ட துறைக்கு,"],
        "intro": [
            "உடனடி கவனம் தேவைப்படும் ஒரு குடிமை சிக்கலை முறையாக புகாரளிக்க இந்தக் கடிதம் எழுதுகிறேன்.",
            "பொது உள்கட்டமைப்பு தொடர்பான ஒரு முக்கியமான விஷயத்தை உங்கள் கவனத்திற்கு கொண்டுவர விரும்புகிறேன்.",
        ],
        "location_prefix": ["சிக்கல் இங்கு காணப்படுகிறது", "இந்தப் பிரச்சினை கீழ்க்கண்ட இடத்தில் கண்டறியப்பட்டது"],
        "action_request": [
            "தயவுசெய்து உங்கள் துறை இந்த இடத்தை ஆய்வு செய்து விரைவில் தீர்வு காணுமாறு கேட்டுக்கொள்கிறேன்.",
            "இந்த விஷயத்தில் முன்னுரிமை அடிப்படையில் நடவடிக்கை எடுக்குமாறு வேண்டுகிறேன்.",
        ],
        "closing": ["உங்கள் உண்மையுள்ள,", "மரியாதையுடன்,", "நன்றியுடன்,"],
        "subject_prefix": "புகார்:",
        "citizen_input_label": "குடிமகனின் கூடுதல் தகவல்",
        "recommendations_label": "பரிந்துரைக்கப்பட்ட திருத்த நடவடிக்கைகள்",
        "tracking_label": "கண்காணிப்பு ஐடி",
        "severity_label": "தீவிரம் மதிப்பெண்",
        "priority_label": "முன்னுரிமை நிலை",
        "location_label": "இடம்",
    },
    "te": {
        "salutation": ["గౌరవనీయులైన మహాశయా/మహాశయులారా,", "గురువర్యులకు,", "సంబంధిత విభాగానికి,"],
        "intro": [
            "తక్షణ దృష్టి అవసరమయ్యే పౌర సమస్యను అధికారికంగా నివేదించడానికి ఈ లేఖ రాస్తున్నాను.",
            "ప్రజా మౌలిక సదుపాయాలకు సంబంధించిన ఒక ముఖ్యమైన విషయాన్ని మీ దృష్టికి తీసుకొస్తున్నాను.",
        ],
        "location_prefix": ["సమస్య ఇక్కడ గుర్తించబడింది", "ఈ సమస్య కింది స్థానంలో కనుగొనబడింది"],
        "action_request": [
            "దయచేసి మీ విభాగం ఈ ప్రదేశాన్ని తనిఖీ చేసి వెంటనే పరిష్కారం చేయాలని కోరుచున్నాను.",
            "ఈ విషయంలో ప్రాధాన్యత ప్రాతిపదికన చర్య తీసుకోవాలని వినమ్రంగా అభ్యర్థిస్తున్నాను.",
        ],
        "closing": ["మీ విశ్వాసపాత్రుడు,", "గౌరవంతో,", "వందనాలతో,"],
        "subject_prefix": "ఫిర్యాదు:",
        "citizen_input_label": "పౌరుడు అందించిన అదనపు సమాచారం",
        "recommendations_label": "సిఫార్సు చేయబడిన సుధారాత్మక చర్యలు",
        "tracking_label": "ట్రాకింగ్ ఐడి",
        "severity_label": "తీవ్రత స్కోర్",
        "priority_label": "ప్రాధాన్యత స్థాయి",
        "location_label": "స్థానం",
    },
    "ml": {
        "salutation": ["ബഹുമാനപ്പെട്ട മഹോദയ/മഹോദയേ,", "ബഹുമാനപ്പെട്ട അധികാരി,", "ബന്ധപ്പെട്ട വകുപ്പിന്,"],
        "intro": [
            "അടിയന്തര ശ്രദ്ധ ആവശ്യമുള്ള ഒരു പൗര പ്രശ്നം ഔദ്യോഗികമായി റിപ്പോർട്ട് ചെയ്യുന്നതിന് ഈ കത്ത് എഴുതുന്നു.",
            "പൊതു അടിസ്ഥാന സൗകര്യങ്ങളുമായി ബന്ധപ്പെട്ട ഒരു പ്രധാനപ്പെട്ട കാര്യം നിങ്ങളുടെ ശ്രദ്ധയിൽ കൊണ്ടുവരാൻ ആഗ്രഹിക്കുന്നു.",
        ],
        "location_prefix": ["പ്രശ്നം ഇവിടെ കണ്ടു", "ഈ പ്രശ്നം താഴെ പറയുന്ന സ്ഥലത്ത് കണ്ടെത്തി"],
        "action_request": [
            "ദയവായി നിങ്ങളുടെ വകുപ്പ് ഈ സ്ഥലം പരിശോധിച്ച് ഉടൻ പരിഹാര നടപടി സ്വീകരിക്കണമെന്ന് അഭ്യർഥിക്കുന്നു.",
            "ഈ കാര്യം മുൻഗണനാ അടിസ്ഥാനത്തിൽ പരിഹരിക്കണമെന്ന് വിനയപൂർവ്വം അഭ്യർഥിക്കുന്നു.",
        ],
        "closing": ["നിങ്ങളുടെ വിശ്വസ്തൻ,", "ആദരവോടെ,", "സ്നേഹ സഹിതം,"],
        "subject_prefix": "പരാതി:",
        "citizen_input_label": "പൗരൻ നൽകിയ അധിക വിവരം",
        "recommendations_label": "ശുപാർശ ചെയ്യപ്പെട്ട തിരുത്തൽ നടപടികൾ",
        "tracking_label": "ട്രാക്കിംഗ് ഐഡി",
        "severity_label": "തീവ്രത സ്കോർ",
        "priority_label": "മുൻഗണന നില",
        "location_label": "സ്ഥലം",
    },
    "mr": {
        "salutation": ["मान्यवर महोदय/महोदया,", "आदरणीय अधिकारी,", "संबंधित विभागास,"],
        "intro": [
            "एका नागरी समस्येबद्दल औपचारिक तक्रार नोंदवण्यासाठी हे पत्र लिहित आहे ज्याकडे त्वरित लक्ष देणे आवश्यक आहे.",
            "सार्वजनिक पायाभूत सुविधांशी संबंधित एक महत्त्वाची बाब आपल्या निदर्शनास आणून देण्यासाठी हे पत्र लिहित आहे.",
        ],
        "location_prefix": ["ही समस्या येथे आढळली आहे", "हा प्रश्न खालील ठिकाणी आढळला"],
        "action_request": [
            "कृपया आपल्या विभागाने या ठिकाणाची पाहणी करून त्वरित उपाययोजना करावी अशी विनंती आहे.",
            "हा प्रश्न प्राधान्याने सोडवण्यात यावा असे नम्रपणे सुचवितो/सुचवते.",
        ],
        "closing": ["आपला/आपली विश्वासू,", "सादर,", "आदरपूर्वक,"],
        "subject_prefix": "तक्रार:",
        "citizen_input_label": "नागरिकाने दिलेली अतिरिक्त माहिती",
        "recommendations_label": "सुचवलेल्या सुधारात्मक कृती",
        "tracking_label": "ट्रॅकिंग आयडी",
        "severity_label": "तीव्रता गुण",
        "priority_label": "प्राधान्य पातळी",
        "location_label": "स्थान",
    },
    "kn": {
        "salutation": ["ಮಾನ್ಯ ಮಹೋದಯ/ಮಹೋದಯೆ,", "ಗೌರವಾನ್ವಿತ ಅಧಿಕಾರಿಗಳೇ,", "ಸಂಬಂಧಿತ ಇಲಾಖೆಗೆ,"],
        "intro": [
            "ತಕ್ಷಣ ಗಮನ ಅಗತ್ಯವಿರುವ ನಾಗರಿಕ ಸಮಸ್ಯೆಯ ಬಗ್ಗೆ ಅಧಿಕೃತವಾಗಿ ದೂರು ದಾಖಲಿಸಲು ಈ ಪತ್ರ ಬರೆಯುತ್ತಿದ್ದೇನೆ.",
            "ಸಾರ್ವಜನಿಕ ಮೂಲ ಸೌಕರ್ಯಗಳಿಗೆ ಸಂಬಂಧಿಸಿದ ಮಹತ್ವದ ವಿಷಯವನ್ನು ನಿಮ್ಮ ಗಮನಕ್ಕೆ ತರಲು ಬಯಸುತ್ತೇನೆ.",
        ],
        "location_prefix": ["ಈ ಸಮಸ್ಯೆ ಇಲ್ಲಿ ಕಂಡುಬಂದಿದೆ", "ಈ ಸಮಸ್ಯೆ ಕೆಳಗಿನ ಸ್ಥಳದಲ್ಲಿ ಗಮನಿಸಲಾಗಿದೆ"],
        "action_request": [
            "ದಯವಿಟ್ಟು ನಿಮ್ಮ ಇಲಾಖೆ ಈ ಸ್ಥಳವನ್ನು ಪರಿಶೀಲಿಸಿ ತ್ವರಿತವಾಗಿ ಸರಿಪಡಿಸಬೇಕು ಎಂದು ವಿನಂತಿಸುತ್ತೇನೆ.",
            "ಈ ವಿಷಯವನ್ನು ಆದ್ಯತೆ ಆಧಾರದ ಮೇಲೆ ಪರಿಹರಿಸಬೇಕೆಂದು ಕೋರುತ್ತೇನೆ.",
        ],
        "closing": ["ನಿಮ್ಮ ವಿಶ್ವಾಸಾರ್ಹ,", "ಗೌರವಪೂರ್ವಕವಾಗಿ,", "ಧನ್ಯವಾದಗಳೊಂದಿಗೆ,"],
        "subject_prefix": "ದೂರು:",
        "citizen_input_label": "ನಾಗರಿಕರ ಹೆಚ್ಚುವರಿ ಮಾಹಿತಿ",
        "recommendations_label": "ಸೂಚಿಸಲಾದ ಸರಿಪಡಿಸುವ ಕ್ರಮಗಳು",
        "tracking_label": "ಟ್ರ್ಯಾಕಿಂಗ್ ಐಡಿ",
        "severity_label": "ತೀವ್ರತೆ ಅಂಕ",
        "priority_label": "ಆದ್ಯತೆ ಮಟ್ಟ",
        "location_label": "ಸ್ಥಳ",
    },
    "gu": {
        "salutation": ["માનનીય મહોદય/મહોદયા,", "આદરણીય અધિકારી,", "સંબંધિત વિભાગને,"],
        "intro": [
            "હું એક નાગરિક સમસ્યાની ઔપચારિક ફરિયાદ નોંધાવવા આ પત્ર લખી રહ્યો/રહી છું જેના પર તાત્કાલિક ધ્યાન આપવું જરૂરી છે.",
            "જાહેર ઇન્ફ્રાસ્ટ્રક્ચરને લગતી એક મહત્ત્વની બાબત આપના ધ્યાન પર લાવવા માટે આ પત્ર લખી રહ્યો/રહી છું.",
        ],
        "location_prefix": ["આ સમસ્યા અહીં જોવા મળી છે", "આ મુદ્દો નીચે દર્શાવેલ સ્થળે જોવામાં આવ્યો"],
        "action_request": [
            "કૃપા કરીને આપના વિભાગ આ સ્થળની તપાસ કરીને વ્હેલી તકે ઉચિત પગલાં ભરવા વિનંતી છે.",
            "આ બાબતનો પ્રાથમિકતાના ધોરણે ઉકેલ લાવવા નમ્ર અનુરોધ છે.",
        ],
        "closing": ["આપનો/આપની વિશ્વાસુ,", "આદરપૂર્વક,", "સ્નેહ સહ,"],
        "subject_prefix": "ફરિયાદ:",
        "citizen_input_label": "નાગરિક દ્વારા આપવામાં આવેલ વધારાની માહિતી",
        "recommendations_label": "સૂચવેલ સુધારાત્મક પગલાં",
        "tracking_label": "ટ્રેકિંગ આઈડી",
        "severity_label": "ગંભીરતા સ્કોર",
        "priority_label": "પ્રાધાન્ય સ્તર",
        "location_label": "સ્થળ",
    },
    "pa": {
        "salutation": ["ਮਾਣਯੋਗ ਮਹੋਦਯ/ਮਹੋਦਯਾ,", "ਆਦਰਯੋਗ ਅਧਿਕਾਰੀ,", "ਸੰਬੰਧਿਤ ਵਿਭਾਗ ਨੂੰ,"],
        "intro": [
            "ਮੈਂ ਇੱਕ ਨਾਗਰਿਕ ਮੁੱਦੇ ਦੀ ਅਧਿਕਾਰਕ ਸ਼ਿਕਾਇਤ ਦਰਜ ਕਰਾਉਣ ਲਈ ਇਹ ਪੱਤਰ ਲਿਖ ਰਿਹਾ/ਰਹੀ ਹਾਂ ਜਿਸ 'ਤੇ ਤੁਰੰਤ ਧਿਆਨ ਦੇਣ ਦੀ ਲੋੜ ਹੈ।",
            "ਜਨਤਕ ਬੁਨਿਆਦੀ ਢਾਂਚੇ ਨਾਲ ਸੰਬੰਧਿਤ ਇੱਕ ਮਹੱਤਵਪੂਰਨ ਵਿਸ਼ੇ ਬਾਰੇ ਤੁਹਾਨੂੰ ਸੂਚਿਤ ਕਰਨਾ ਚਾਹੁੰਦਾ/ਚਾਹੁੰਦੀ ਹਾਂ।",
        ],
        "location_prefix": ["ਇਹ ਸਮੱਸਿਆ ਇੱਥੇ ਦੇਖੀ ਗਈ ਹੈ", "ਇਹ ਮੁੱਦਾ ਹੇਠਾਂ ਦੱਸੀ ਥਾਂ 'ਤੇ ਪਾਇਆ ਗਿਆ"],
        "action_request": [
            "ਬੇਨਤੀ ਹੈ ਕਿ ਤੁਹਾਡਾ ਵਿਭਾਗ ਇਸ ਸਥਾਨ ਦੀ ਜਾਂਚ ਕਰਕੇ ਜਲਦੀ ਤੋਂ ਜਲਦੀ ਢੁੱਕਵੇਂ ਕਦਮ ਚੁੱਕੇ।",
            "ਇਸ ਮਾਮਲੇ ਨੂੰ ਤਰਜੀਹੀ ਆਧਾਰ 'ਤੇ ਹੱਲ ਕੀਤਾ ਜਾਵੇ।",
        ],
        "closing": ["ਤੁਹਾਡਾ/ਤੁਹਾਡੀ ਵਿਸ਼ਵਾਸਪਾਤਰ,", "ਆਦਰ ਸਹਿਤ,", "ਧੰਨਵਾਦ ਸਹਿਤ,"],
        "subject_prefix": "ਸ਼ਿਕਾਇਤ:",
        "citizen_input_label": "ਨਾਗਰਿਕ ਵੱਲੋਂ ਦਿੱਤੀ ਗਈ ਵਾਧੂ ਜਾਣਕਾਰੀ",
        "recommendations_label": "ਸੁਝਾਏ ਗਏ ਸੁਧਾਰਾਤਮਕ ਕਦਮ",
        "tracking_label": "ਟ੍ਰੈਕਿੰਗ ਆਈਡੀ",
        "severity_label": "ਗੰਭੀਰਤਾ ਸਕੋਰ",
        "priority_label": "ਤਰਜੀਹ ਪੱਧਰ",
        "location_label": "ਸਥਾਨ",
    },
    "ur": {
        "salutation": ["محترم جناب/محترمہ,", "قابل احترام افسر,", "متعلقہ محکمے کو,"],
        "intro": [
            "میں ایک شہری مسئلے کی باضابطہ شکایت درج کرانے کے لیے یہ خط لکھ رہا/رہی ہوں جس پر فوری توجہ کی ضرورت ہے۔",
            "عوامی بنیادی ڈھانچے سے متعلق ایک اہم معاملے کی طرف آپ کی توجہ دلانا چاہتا/چاہتی ہوں۔",
        ],
        "location_prefix": ["یہ مسئلہ یہاں دیکھا گیا ہے", "یہ مسئلہ درج ذیل مقام پر دیکھا گیا"],
        "action_request": [
            "گزارش ہے کہ آپ کا محکمہ اس مقام کا معائنہ کرکے فوری اصلاحی اقدامات کرے۔",
            "اس معاملے کو ترجیحی بنیادوں پر حل کیا جائے۔",
        ],
        "closing": ["آپ کا/آپ کی مخلص,", "با ادب,", "سادر,"],
        "subject_prefix": "شکایت:",
        "citizen_input_label": "شہری کی طرف سے دی گئی اضافی معلومات",
        "recommendations_label": "تجویز کردہ اصلاحی اقدامات",
        "tracking_label": "ٹریکنگ آئی ڈی",
        "severity_label": "شدت سکور",
        "priority_label": "ترجیح کی سطح",
        "location_label": "مقام",
    },
}

_TONE_URGENCY = {
    "formal": {"en": "This issue requires timely attention and resolution.", "hi": "इस समस्या के समाधान की आवश्यकता है।", "bn": "এই সমস্যার সমাধান প্রয়োজন।", "ta": "இந்த சிக்கல் தீர்வு தேவை.", "te": "ఈ సమస్య పరిష్కారం అవసరం.", "ml": "ഈ പ്രശ്നം പരിഹരിക്കേണ്ടതുണ്ട്.", "mr": "या समस्येचे निराकरण आवश्यक आहे.", "kn": "ಈ ಸಮಸ್ಯೆ ಪರಿಹಾರ ಅಗತ್ಯ.", "gu": "આ સમસ્યાનો ઉકેલ જરૂરી છે.", "pa": "ਇਸ ਸਮੱਸਿਆ ਦਾ ਹੱਲ ਜ਼ਰੂਰੀ ਹੈ।", "ur": "اس مسئلے کا حل ضروری ہے۔"},
    "urgent": {"en": "⚠️ This is URGENT — please treat this as a high-priority emergency requiring immediate action.", "hi": "⚠️ यह अत्यंत जरूरी है — कृपया इसे उच्च प्राथमिकता से तत्काल संभालें।", "bn": "⚠️ এটি জরুরি — অনুগ্রহ করে এটিকে উচ্চ অগ্রাধিকারের জরুরি অবস্থা হিসেবে বিবেচনা করুন।", "ta": "⚠️ இது அவசரம் — தயவுசெய்து இதை உயர் முன்னுரிமை அவசரநிலையாக கையாளுங்கள்.", "te": "⚠️ ఇది అత్యవసరం — దయచేసి దీన్ని అధిక ప్రాధాన్యత అత్యవసర పరిస్థితిగా పరిగణించండి.", "ml": "⚠️ ഇത് അടിയന്തരമാണ് — ദയവായി ഇത് ഉയർന്ന മുൻഗണനയുള്ള അടിയന്തരാവസ്ഥയായി കൈകാര്യം ചെയ്യുക.", "mr": "⚠️ हे अत्यंत तातडीचे आहे — कृपया उच्च प्राधान्याने तत्काळ उपाययोजना करा.", "kn": "⚠️ ಇದು ತುರ್ತು — ದಯವಿಟ್ಟು ಇದನ್ನು ಹೆಚ್ಚಿನ ಆದ್ಯತೆಯ ತುರ್ತು ಸ್ಥಿತಿಯಾಗಿ ಪರಿಗಣಿಸಿ.", "gu": "⚠️ આ તાત્કાલિક છે — કૃપા કરીને ઉચ્ચ પ્રાથમિકતા સાથે તુરંત પગલું ભરો.", "pa": "⚠️ ਇਹ ਜ਼ਰੂਰੀ ਹੈ — ਕਿਰਪਾ ਕਰਕੇ ਇਸ ਨੂੰ ਉੱਚ ਤਰਜੀਹ ਦੇ ਅਧਾਰ 'ਤੇ ਤੁਰੰਤ ਹੱਲ ਕਰੋ।", "ur": "⚠️ یہ انتہائی فوری ہے — براہ کرم اسے اعلی ترجیح کی ہنگامی صورتحال کے طور پر ہینڈل کریں۔"},
    "escalated": {"en": "🚨 ESCALATION NOTICE: Previous reports on similar issues in this area have gone unresolved. This is a formal escalation demanding immediate executive intervention.", "hi": "🚨 ध्यान दें: इस क्षेत्र में पहले की रिपोर्टें अनसुलझी रही हैं। यह औपचारिक एस्केलेशन है।", "bn": "🚨 এই এলাকায় পূর্ববর্তী রিপোর্ট অমীমাংসিত রয়েছে। এটি একটি আনুষ্ঠানিক এস্কেলেশন।", "ta": "🚨 இந்த பகுதியில் முந்தைய அறிக்கைகள் தீர்க்கப்படவில்லை. இது ஒரு முறையான நிலை உயர்வு.", "te": "🚨 ఈ ప్రాంతంలో మునుపటి నివేదికలు పరిష్కరించబడలేదు. ఇది అధికారిక ఎస్కలేషన్.", "ml": "🚨 ഈ പ്രദേശത്ത് മുൻ റിപ്പോർട്ടുകൾ പരിഹരിക്കപ്പെട്ടിട്ടില്ല. ഇത് ഒരു ഔദ്യോഗിക ഉന്നയനമാണ്.", "mr": "🚨 या क्षेत्रातील मागील तक्रारी अनुत्तरित राहिल्या आहेत. हे औपचारिक एस्केलेशन आहे.", "kn": "🚨 ಈ ಪ್ರದೇಶದ ಹಿಂದಿನ ವರದಿಗಳು ಪರಿಹರಿಸಲ್ಪಟ್ಟಿಲ್ಲ. ಇದು ಅಧಿಕೃತ ಎಸ್ಕಲೇಷನ್.", "gu": "🚨 આ વિસ્તારની અગાઉની ફરિયાદો અઉકેલ્ઈ છે. આ ઔપચારિક એસ્કેલেશન છે.", "pa": "🚨 ਇਸ ਖੇਤਰ ਵਿੱਚ ਪਹਿਲਾਂ ਦੀਆਂ ਸ਼ਿਕਾਇਤਾਂ ਅਣਸੁਲਝੀਆਂ ਰਹੀਆਂ ਹਨ। ਇਹ ਰਸਮੀ ਐਸਕੇਲੇਸ਼ਨ ਹੈ।", "ur": "🚨 اس علاقے میں پہلی رپورٹیں حل نہیں ہوئیں۔ یہ ایک باضابطہ ایسکلیشن ہے۔"},
}


def _pick(lst: list[str]) -> str:
    return random.choice(lst)


def _sanitize_text(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def generate_letter(
    *,
    tracking_id: str,
    language: str,
    tone: str,
    issue_category: str | None,
    department_name: str | None,
    ward: str | None,
    locality: str | None,
    jurisdiction: str | None,
    latitude: float | None,
    longitude: float | None,
    severity_score: float | None,
    priority: int | None,
    citizen_description: str | None,
    recommendations: list[str],
    reporter_name: str | None = None,
    detected_issues: list[dict] | None = None,
) -> LetterDraft:
    lang = (language or "en").lower().strip()
    if lang not in _PHRASES:
        lang = "en"

    p = _PHRASES[lang]
    tone_norm = (tone or "formal").lower().strip()
    if tone_norm not in _TONE_URGENCY:
        tone_norm = "formal"

    issue = (issue_category or "public_hazard").replace("_", " ")
    dep = department_name or "Public Works / Municipal Department"
    sev = severity_score if severity_score is not None else 0.0
    pr = priority if priority is not None else 3
    loc_parts = [x for x in [locality, ward, jurisdiction] if x]
    loc = ", ".join(loc_parts) if loc_parts else None
    citizen_text = _sanitize_text(citizen_description) if citizen_description else ""
    recs_list = (recommendations or [])[:5]
    d_issue_desc = detected_issues[0].get("description", "") if detected_issues and len(detected_issues)>0 else ""

    actual_language_name = LANGUAGE_NAME_MAP.get(lang, "English")

    final_reporter_name = "Concerned Citizen"
    if reporter_name and reporter_name.strip():
        final_reporter_name = reporter_name.strip()

    if settings.gemini_api_key:
        try:
            from google import genai
            from google.genai import types as genai_types

            print(f"[NLP] Generating letter — lang={lang} ({actual_language_name}), reporter={final_reporter_name!r}")

            client = genai.Client(api_key=settings.gemini_api_key)
            system_instruction = (
                f"You are a professional multilingual complaint letter writer. "
                f"You MUST write ALL output exclusively in {actual_language_name}. "
                f"Do NOT use English except for proper nouns, tracking codes, and technical terms. "
                f"Do NOT add any language disclaimer or translation note."
            )
            prompt = f"""Write a highly professional civic complaint letter addressed to {dep}.

Tone: {tone_norm}

Details:
- Issue Category: {issue}
- Specific AI Visual Detection: {d_issue_desc}
- Citizen's Own Description: {citizen_text}
- Location: {loc} (Coordinates: {latitude}, {longitude})
- Severity Score (0-1): {sev}
- Recommended Actions: {', '.join(recs_list)}
- Tracking ID: {tracking_id}
- Account Holder / Complainant: {final_reporter_name}

Instructions:
1. Start with SUBJECT: on the first line.
2. Write a unique, narrative-driven letter — weave the AI detection and citizen's description naturally. No fill-in-the-blank templates.
3. Match the tone ({tone_norm}): formal=professional, urgent=alarm-raising, escalated=demanding executive review.
4. Include Tracking ID and Severity Score naturally within the letter body.
5. Close with recommendations as a numbered list.
6. Sign off exclusively as: {final_reporter_name}
   (Do not use any other name. Do NOT write CivicSentinel Citizen or Concerned Citizen.)
"""
            resp = client.models.generate_content(
                model='gemini-2.0-flash-lite',
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.8,
                )
            )
            text = resp.text.strip()

            subject = f"Complaint: {issue.title()} — {tracking_id}"
            body_text = text
            if "SUBJECT:" in text.upper()[:200]:
                lines = text.split("\n", 1)
                subject = lines[0].replace("SUBJECT:", "").replace("Subject:", "").strip()
                body_text = lines[1].strip() if len(lines) > 1 else text

            return LetterDraft(subject=subject, body=body_text)
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                print(f"[NLP] Gemini quota exceeded, using multilingual template.")
            elif "503" in err_str or "UNAVAILABLE" in err_str:
                print(f"[NLP] Gemini temporarily unavailable, using multilingual template.")
            else:
                print(f"[NLP] Gemini error: {e}, using multilingual template.")

    issue = (issue_category or "public_hazard").replace("_", " ")
    dep = department_name or "Public Works / Municipal Department"
    sev = severity_score if severity_score is not None else 0.0
    pr = priority if priority is not None else 3
    loc_parts = [x for x in [locality, ward, jurisdiction] if x]
    loc = ", ".join(loc_parts) if loc_parts else None
    coords = (
        f"{latitude:.5f}, {longitude:.5f}"
        if latitude is not None and longitude is not None
        else None
    )

    citizen_text = _sanitize_text(citizen_description) if citizen_description else ""
    recs_list = (recommendations or [])[:5]

    # Build subject
    subject = f"{p['subject_prefix']} {issue.title()} — {tracking_id}"

    # Build body
    lines = [
        f"{dep}\n",
        _pick(p["salutation"]),
        "",
        _pick(p["intro"]),
        "",
        _TONE_URGENCY[tone_norm].get(lang, _TONE_URGENCY[tone_norm]["en"]),
        "",
    ]

    # Location block
    if loc or coords:
        loc_line = f"{_pick(p['location_prefix'])}: {loc or ''}"
        if coords:
            loc_line += f" ({coords})"
        lines.append(loc_line)

    # Severity + priority
    lines += [
        "",
        f"{p['severity_label']}: {sev:.2f} | {p['priority_label']}: {pr}",
        "",
    ]

    # AI Detection details
    if d_issue_desc:
        lines += [f"{p['citizen_input_label']} (AI):", d_issue_desc, ""]

    # Citizen description
    if citizen_text:
        lines += [f"{p['citizen_input_label']}:", citizen_text, ""]

    # Recommendations
    if recs_list:
        lines.append(f"{p['recommendations_label']}:")
        for r in recs_list:
            lines.append(f"  • {r}")
        lines.append("")

    # Action request + closing
    lines += [
        _pick(p["action_request"]),
        "",
        f"{p['tracking_label']}: {tracking_id}",
        "",
        _pick(p["closing"]),
        final_reporter_name,
    ]

    body = "\n".join(lines)
    return LetterDraft(subject=subject, body=body)
