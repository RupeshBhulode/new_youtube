

# Question keywords
question_keywords = [
    # Common English question patterns
    "how", "what", "why", "when", "where", "which",
    "who", "is it", "can I", "do I", "should I", "will it",
    "does it", "could I", "am I", "are we", "have to",
    "how do I", "how can I", "anyone know", "any idea",
    "please explain", "can someone", "need help with", "how to",

    # Hindi / Hinglish questions
    "kaise", "kyu", "kab", "kaha", "kya", "konsa", "kis tarah",
    "mujhe samajh nahi aaya", "kaise kare", "samjhao", "bataiye",
    "kya yeh sahi hai", "kya main", "kya yeh", "kya ho sakta hai",
    "kaise ho", "kaise hoga", "kaise sikhe", "kaise banaen",

    # Mixed Hinglish and informal
    "pls help", "pls explain", "pls reply", "bhai samjha do", "bhaiya reply",
    "sir reply", "sir please", "bro help", "query", "doubt",
    "question", "confused", "pata nahi chal raha", "kaise shuru karein",
    "start kaise kare", "guide karo", "problem ho rahi hai", "ye kaise hota hai",

    # Emojis and emotion-based phrases (intent detection)
    "❓", "🤔", "🙏", "😢", "please?", "any advice?", "help!", "suggest?", "urgent question"
]

# Request keywords
request_keywords = [
    # ✅ English Requests
    "please make", "please upload", "please add", "please explain", "please do", 
    "can you", "could you", "would you", "make a video", "bring a course", 
    "kindly share", "kindly upload", "need video", "need tutorial", 
    "need course", "pls make", "pls upload", "pls share", "pls explain",
    "want video on", "want to learn", "I request", "request you to",

    # ✅ Hindi Requests (transliterated)
    "kripya", "banaiye", "banao", "le aaiye", "sikhaiye", "upload kijiye", 
    "please banao", "ek video banao", "mujhe chahiye", "mujhe sikhna hai", 
    "video chahiye", "course le aaiye", "pls sikhao", "mujhe samjhao", 
    "ek baar samjha do", "mujhe bhi sikhao", "batayiye", "mujhe chahiye",

    # ✅ Hinglish / Mixed Casual
    "video lao", "course lao", "bro banao", "harry bhai video lao", "ek aur video banao",
    "bhai please", "bhai banao", "sir pls", "sir request", "sir ek bar", 
    "bhai video banao", "please bhai", "please sir", "guide kar do", 
    "plzz banao", "video chahiye bhai", "coding sikhao", "project banao",

    # ✅ Emojis / Implicit Emotional Cues
    "🙏", "😢", "🥺", "❤️ request", "plzzzz", "sir 😭", "please 😭", 
    "bhot jaruri hai", "help chahiye", "video bana do bhai", "sir 😢",

    # ✅ Repeated / stylized forms
    "plzz", "plzzz", "plssss", "plspls", "sir plzz", "req", "urgent need", 
    "abhi chahiye", "asap video", "jaldi lao", "abhi banao", "turant chahiye"
]

# Feedback keywords
feedback_keywords = [
    # ✅ English feedback & praise
    "thank you", "thanks a lot", "thank you so much", "helped me a lot", 
    "very helpful", "super helpful", "really appreciate", "best video", 
    "awesome work", "great work", "great content", "amazing content", 
    "love your videos", "you’re the best", "my favorite channel", 
    "you helped me", "life saver", "good explanation", "very informative", 
    "easy to understand", "very clear", "keep it up", "well explained",

    # ✅ Hindi / Hinglish (transliterated feedback)
    "bahut badiya", "bhai mast video", "bahut accha samjhaya", 
    "mast content", "bhot accha", "shandaar", "bahut badhiya", 
    "aapka video bhot accha laga", "samajh aa gaya", "clear ho gaya", 
    "aapka course best hai", "bhot useful tha", "bhot maza aaya", 
    "bhot knowledge mila", "maza aa gaya", "mujhe bahut accha laga", 
    "bhai op", "bhai fire ho", "aapka content next level hai",

    # ✅ Hinglish short praises
    "op work", "next level content", "fire video", "goat creator", 
    "bhai fire ho", "bhai OP", "legend bro", "sahi bata rahe ho", 
    "respect bro", "bhai superb", "nice explanation bhai", 
    "bohot accha explain kiya", "bahut hi badiya kaam", 
    "bhai kamal ho", "bhai king ho",

    # ✅ Emojis & positive emotional tone
    "🔥", "❤️", "❤️", "💯", "👍", "🥰", "🙌", "👏", "😊", "🙏", "😍", 
    "💖", "💥", "🤩", "⭐", "✨", "OP🔥", "🚀", "legend", "king 👑",

    # ✅ Review or reflection based
    "learnt a lot", "changed my life", "was confused before this", 
    "watched full video", "amazing teaching style", "finally understood", 
    "watched 10 times", "completed the course", "better than others", 
    "inspired me", "recommend to everyone", "subscribed because of this", 
    "never seen anything this clear", "best tutorial", "this helped me crack interview"
]



def filter_questions(comments):
    matched = []
    for c in comments:
        lower_c = c.lower()
        if any(k in lower_c for k in question_keywords):
            matched.append(c)
    if len(matched)>=10:        
        return matched
    else:
        return comments[:10]

def filter_requests(comments):
    matched = []
    for c in comments:
        lower_c = c.lower()
        if any(k in lower_c for k in request_keywords):
            matched.append(c)
    if len(matched)>=10:        
        return matched
    else:
        return comments[:10]

def filter_feedbacks(comments):
    matched = []
    for c in comments:
        lower_c = c.lower()
        if any(k in lower_c for k in feedback_keywords):
            matched.append(c)
    if len(matched)>=10:        
        return matched
    else:
        return comments[:10]

