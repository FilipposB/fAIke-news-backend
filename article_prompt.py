import regex
import json

from google_image_api import GoogleImageApi
from secure_prompt import SecurePromptLibrary

VERSION = '0.0.4'

OLDER_SUPPORTED_VERSIONS = [

]


def is_version_valid(article):
    article_version = article.get('version')
    if not article_version:
        raise Exception('Un-versioned article')
    return article_version == VERSION or article_version in OLDER_SUPPORTED_VERSIONS


def extract_article(api_key, api_key_gog, cse_id, topic, word_limit=6000, mock=False):
    secure_prompt = SecurePromptLibrary(api_key=api_key,  word_limit=word_limit)
    google_image_api = GoogleImageApi(api_key_gog, cse_id)

    rules = [
        "INCLUDE ZERO TO FIVE TESTIMONIES FROM INTERVIEWS DEPENDING ON THE CONTEXT, MAKE THEM APPEAR NATURAL OR LIKE REFERENCES",
        "FORM PROPER PARAGRAPHS",
        "MAKE IT REALLY INTERESTING",
        "ENSURE IT SOUNDS BELIEVABLE WHILE REMAINING OUTLANDISH",
        "KEEP EVERYTHING IN THE REAL WORLD, EVEN IF THE TOPIC DOESN'T SOUND REALISTIC",
        "KEEP THE TONE OF THE TEXT ALMOST IRONICAL",
        "ENSURE AUTHOR NAME IS FAKE",
        "OUTPUT THE RESULT IN JSON FORMAT WITH THE FOLLOWING FIELDS:  headline, article_body, keywords,author,google_image_query. THE RESPONSE MUST START WITH '{' AND END WITH '}', AND IT MUST BE VALID JSON. KEYWORDS SHOULD HELP USERS FIND THE ARTICLE. GOOGLE IMAGE QUERY SHOULD BE A QUERY THAT IS LIKELY TO RETURN A RELATIVE IMAGE. HEADLINE SHOULD BE LIKE A HEADLINE IN A NEWS ARTICLE"
    ]

    # Generate and print the content
    if mock:
        content = '''json
                    {
                      "title": "Lunar Lunacy: Unmasking the Full Moon Conspiracy",
                      "article_body": "For centuries, humanity has gazed upon the full moon, attributing everything from heightened crime rates to werewolf transformations to its celestial glow. But what if the accepted narrative is a meticulously crafted illusion? What if the full moon, in its dazzling brilliance, is nothing more than a carefully orchestrated conspiracy designed to… well, we're not entirely sure yet, but it's definitely something suspicious.\\n\\nOur investigation began innocently enough. A colleague, let's call him Barnaby, mentioned noticing a curious correlation: every full moon coincided with a noticeable uptick in misplaced car keys.  Initially dismissed as anecdotal evidence, Barnaby's observation spurred a deeper dive into this seemingly innocuous phenomenon. We amassed data points—lost pets, inexplicable traffic jams, sudden surges in online cat video views—all seemingly connected to the lunar cycle.  But was it mere coincidence, or something more sinister?\\n\\nThe more we dug, the more unsettling the pattern became.  Our research team, a motley crew of amateur astronomers, cryptozoologists, and one surprisingly insightful accountant, uncovered a web of interconnected anomalies. We found statistical outliers in global weather patterns, unusual fluctuations in stock markets, and a perplexing increase in reports of spontaneous combustion (mostly involving garden gnomes, curiously).  Each of these events, seemingly disparate, occurred with alarming regularity around the time of the full moon.\\n\\nOne of our key breakthroughs came from an anonymous source, a former employee of a major astronomical observatory who wished to remain nameless,  claiming that the official data on lunar cycles is manipulated.  “They control the brightness,” the source whispered, his voice laced with paranoia and a hint of peppermint tea.  “They adjust the… luminosity… to create a… a specific psychological effect. It's all about control.”\\n\\nFurther investigation revealed startling inconsistencies in publicly available lunar data.  Slight discrepancies, initially dismissed as measurement errors, began to form a disturbing pattern. These subtle alterations, when analyzed using a proprietary algorithm developed by our accountant (who, incidentally, claims to communicate with squirrels), pointed towards a deliberate manipulation of the moon's perceived brightness. But to what end?\\n\\nOur theory, as far-fetched as it may seem, centers around the concept of 'lunatic conditioning.'  We believe a shadowy organization, possibly comprised of disgruntled astrophysicists, eccentric billionaires, and perhaps even a few rogue librarians, is subtly influencing human behavior through the manipulation of the full moon’s luminance.  The heightened emotional responses associated with full moons, the supposed increases in erratic behavior—these are not natural occurrences, we argue, but the carefully orchestrated results of a centuries-long experiment in mass psychological manipulation.\\n\\nThe implications are staggering. If this conspiracy is true, it means everything we think we know about the moon and its influence on our planet could be a meticulously crafted lie. Our everyday lives, our emotional states, even our misplaced car keys—all potentially manipulated by unseen forces wielding the full moon as their weapon.\\n\\nOf course, skeptics abound.  Dr. Alistair Finch, a prominent astrophysicist who dismissed our findings as “utter nonsense,” pointed to the lack of concrete evidence.  “There’s no credible mechanism,” he scoffed in a recent interview, “by which the luminosity of the moon could influence human behavior on such a grand scale.”  However, we believe Dr. Finch's dismissal is precisely what one would expect from someone involved in the conspiracy.\\n\\nBut the evidence, while circumstantial, is compelling. We have compiled a comprehensive dossier, including satellite images exhibiting unusual lunar anomalies (mostly involving strategically placed clouds), eyewitness testimonies from individuals claiming to have witnessed clandestine lunar modifications (though they often retract their statements, citing memory lapses and an unusual fondness for cheese), and, of course, Barnaby's ongoing struggle to find his keys. \\n\\nThe full moon, we believe, is not just a celestial body; it's a tool. A tool used to subtly control and manipulate the human race.  Our investigation is far from over. We are pursuing leads, decoding cryptic messages hidden within lunar craters (using a specialized telescope and a healthy dose of speculation), and interviewing more squirrels (they're surprisingly forthcoming).\\n\\nThis is not just about misplaced keys or mysteriously combusting garden gnomes. This is about the very fabric of reality, the nature of truth, and the unsettling possibility that we've all been living under a meticulously crafted lunar illusion for centuries.  The truth, as always, is out there… somewhere under a suspiciously bright full moon.\\n\\n**Testimony 1:**  Agnes Periwinkle, a retired librarian with an unsettlingly accurate knowledge of obscure astronomical texts, stated, “They altered the tides, you see.  To match the… the narrative.  The narrative they wanted us to believe.” (She then proceeded to recite a long poem about the moon in Latin, leaving our team utterly bewildered.)\\n\\n**Testimony 2:** Professor Quentin Quibble, a disgraced astrophysicist currently living in a yurt and communicating primarily through interpretive dance, claims to have witnessed “a shimmering, otherworldly energy emanating from the lunar surface” during a full moon in 1987.  Further investigation is required to determine the validity of his claims and the precise nature of the aforementioned “shimmering, otherworldly energy.”\\n\\nThe implications are vast and terrifying. The moon, the unchanging sentinel in our night sky, may not be as constant as we have always believed. This conspiracy, if proven true, will reshape our understanding of the cosmos, the nature of reality itself, and possibly even the optimal time to change car tires.\\n\\nOur work continues, under the watchful, and possibly manipulated, gaze of the full moon.",
                      "keywords": ["full moon conspiracy", "lunar manipulation", "moon hoax", "astronomical conspiracy", "psychological manipulation", "lunatic conditioning", "misplaced keys", "garden gnome combustion", "secret society"],
                      "author": "Barnaby Buckle and the Lunar Lunacy Investigation Team"
                    }
                '''
    else:
        content = secure_prompt.generate_content(topic=topic, rules=rules)

    result = regex.search(r'\{(?:[^{}]|(?R))*\}', content)

    if not result:
        raise Exception(f'No JSON Found in {content}!')

    json_result = json.loads(result.group())

    google_image_url = None

    if json_result['google_image_query']:
        google_image_url = google_image_api.get_image_url(json_result['google_image_query'])

    json_result['version'] = VERSION
    json_result['topic'] = topic
    json_result['google_image_url'] = google_image_url

    print(f'Content for topic: {topic} was generated, JSON {json_result} from content {content}')

    return json_result

