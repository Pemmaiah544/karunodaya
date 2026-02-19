import random

READING_PASSAGES = {
    'EN': {
        'PRE_K': [
            {
                'title': 'The Happy Cat',
                'text': 'The cat is red. The cat is fat. The cat sat on the mat. The cat is happy.',
                'word_count': 18,
                'theme': 'animals'
            },
            {
                'title': 'My Big Dog',
                'text': 'I have a big dog. The dog is brown. He likes to run and play in the sun.',
                'word_count': 17,
                'theme': 'animals'
            },
            {
                'title': 'The Star',
                'text': 'I see a star. The star is big. It is up in the sky. I like the star.',
                'word_count': 18,
                'theme': 'space'
            },
            {
                'title': 'The Little Boat',
                'text': 'I have a boat. The boat is blue. It goes on the water. I sail far away.',
                'word_count': 18,
                'theme': 'adventure'
            },
            {
                'title': 'The Fairy Wing',
                'text': 'I found a wing. It is pink and small. A fairy left it here. Now I can fly!',
                'word_count': 18,
                'theme': 'fairy_tales'
            }
        ],
        'KINDERGARTEN': [
            {
                'title': 'My Little Tree',
                'text': 'I have a little tree. It is green and brown. It grows in the sun. I water my tree every day. It makes me smile.',
                'word_count': 26,
                'theme': 'adventure'
            },
            {
                'title': 'The Blue Boat',
                'text': 'We have a blue boat. The boat is on the water. We like to fish in the lake. The water is cold.',
                'word_count': 21,
                'theme': 'adventure'
            },
            {
                'title': 'The Baby Rabbit',
                'text': 'A baby rabbit lives in my garden. It has soft white fur and long ears. It eats the green leaves every morning.',
                'word_count': 22,
                'theme': 'animals'
            },
            {
                'title': 'The Moon',
                'text': 'The moon is big and round tonight. It shines on my bed. I wave to the moon. The moon waves back at me.',
                'word_count': 22,
                'theme': 'space'
            },
            {
                'title': 'The Magic Flower',
                'text': 'A tiny flower grew in the garden. It was gold and shiny. When I touched it, it sang a little song to me.',
                'word_count': 23,
                'theme': 'fairy_tales'
            }
        ],
        'GRADE_1': [
            {
                'title': 'The Brave Little Kite',
                'text': '"I never can do it," the little kite said, as he looked at the others high over his head. "I know I should fall if I tried to fly." "Try," said the big kite; "only try! Or I fear you never will learn at all."',
                'word_count': 45,
                'theme': 'adventure'
            },
            {
                'title': 'Sunny Day',
                'text': 'The sun is out today. I went to the park with my mom. We saw a red bird in the tree. It sang a sweet song. I was very happy to be outside.',
                'word_count': 33,
                'theme': 'animals'
            },
            {
                'title': 'My Rocket Ship',
                'text': 'I built a rocket ship from a big box. I sat inside and counted down. Three, two, one, blast off! I flew past the moon and the stars. Then I came home for dinner.',
                'word_count': 35,
                'theme': 'space'
            },
            {
                'title': 'The Wishing Well',
                'text': 'There was an old well behind the hill. People said it was magic. I threw a coin inside and made a wish. The next day, a rainbow appeared over my house.',
                'word_count': 33,
                'theme': 'fairy_tales'
            }
        ],
        'GRADE_2': [
            {
                'title': 'A Summer Day',
                'text': 'The sun was shining brightly as the children ran to the park. They wanted to play on the swings and slide. Sarah found a beautiful butterfly in the grass. It was blue and orange. She watched it fly away into the clear blue sky.',
                'word_count': 48,
                'theme': 'adventure'
            },
            {
                'title': 'The Lost Puppy',
                'text': 'Tom found a small brown puppy near the school gate. It had no collar and looked very hungry. He gave it some bread from his lunch box. The puppy wagged its tail and licked his hand. Tom took the puppy home and named it Biscuit.',
                'word_count': 46,
                'theme': 'animals'
            },
            {
                'title': 'Rainy Morning',
                'text': 'It was raining hard when Priya woke up. She put on her yellow raincoat and red boots. She splashed in every puddle on the way to school. Her friends laughed and joined her. They had the best morning ever.',
                'word_count': 40,
                'theme': 'adventure'
            },
            {
                'title': 'The Night Sky',
                'text': 'Aman looked up at the sky through his telescope. He could see the rings of Saturn and the red spot on Jupiter. His father told him that each star was a sun far away. Aman dreamed of visiting them one day.',
                'word_count': 42,
                'theme': 'space'
            },
            {
                'title': 'The Talking Fish',
                'text': 'One day a fisherman caught a golden fish. The fish opened its mouth and said please let me go. The fisherman was so surprised that he dropped the net. The fish thanked him and swam away into the deep blue sea.',
                'word_count': 42,
                'theme': 'fairy_tales'
            },
            {
                'title': 'The Parrot Who Sang',
                'text': 'Riya had a green parrot named Mittu. Every morning Mittu would sing songs and copy what Riya said. One day Mittu learned to say good morning to everyone who visited. All the neighbours loved hearing his cheerful voice.',
                'word_count': 40,
                'theme': 'animals'
            }
        ],
        'GRADE_3': [
            {
                'title': 'The Magic Forest',
                'text': 'Deep in the heart of the ancient forest, there lived a small squirrel named Nutty. Nutty was not like other squirrels because he loved to collect shiny smooth stones instead of acorns. One morning, he discovered a stone that pulsed with a soft, green light. When he touched it, the trees began to whisper secrets of old magic.',
                'word_count': 64,
                'theme': 'fairy_tales'
            },
            {
                'title': 'The Kite Festival',
                'text': 'Every year, the whole town gathered on the big hill for the kite festival. Children brought kites of all shapes and sizes. Ravi had made his kite from old newspapers and bamboo sticks. When the wind picked up, his kite soared higher than all the others. Everyone cheered and clapped as it danced across the bright blue sky.',
                'word_count': 60,
                'theme': 'adventure'
            },
            {
                'title': 'The Clever Crow',
                'text': 'A thirsty crow found a tall jar with water at the very bottom. He could not reach it with his beak. Then he had a clever idea. He picked up small stones one by one and dropped them into the jar. Slowly the water rose higher and higher until the crow could drink it easily.',
                'word_count': 56,
                'theme': 'animals'
            },
            {
                'title': 'Mission to Mars',
                'text': 'The astronauts strapped themselves into the rocket as the countdown began. In just ten seconds they would leave Earth for the very first time. The engines roared and the rocket shot into the sky. Through the small round window they watched the blue planet get smaller and smaller below them.',
                'word_count': 52,
                'theme': 'space'
            },
            {
                'title': 'The River Adventure',
                'text': 'Kiran and his sister built a raft from old wooden planks and rope. They pushed it into the river and climbed aboard. The water carried them past green fields and under stone bridges. A family of ducks swam alongside them for a while. It was the best adventure of the summer holidays.',
                'word_count': 52,
                'theme': 'adventure'
            },
            {
                'title': 'The Enchanted Lamp',
                'text': 'In a dusty corner of the old market, Anaya found a copper lamp covered in strange symbols. When she rubbed it clean with her sleeve, a tiny spark of light floated out and danced around her head. The light whispered that it would grant her one wish if she could solve its riddle.',
                'word_count': 52,
                'theme': 'fairy_tales'
            }
        ],
        'GRADE_4': [
            {
                'title': 'Space Explorer',
                'text': 'Captain Leo adjusted his helmet as the spaceship prepared for landing. He had traveled millions of miles across the galaxy to reach the mysterious red planet. Through the thick glass of the viewport, he could see towering mountains and vast plains of crimson dust. This was the first time any human had ever set foot on this distant world.',
                'word_count': 66,
                'theme': 'space'
            },
            {
                'title': 'The Jungle Rescue',
                'text': 'Meera and her grandfather walked carefully through the dense forest. They had heard about a baby elephant trapped near the river bank. After an hour of searching, they found it stuck in thick mud. Meera called the forest ranger on her phone while her grandfather kept the frightened animal calm. Together they pulled the elephant free before sunset.',
                'word_count': 62,
                'theme': 'animals'
            },
            {
                'title': 'The Science Fair',
                'text': 'Arjun spent three weeks building a model volcano for the science fair. He used baking soda and vinegar to make it erupt with red foam. On the day of the fair, the judges were amazed by the realistic lava flow. His project won first prize and his teacher said it was the best demonstration she had ever seen.',
                'word_count': 60,
                'theme': 'adventure'
            },
            {
                'title': 'The Sleeping Dragon',
                'text': 'High on the misty mountain, the villagers believed a dragon slept inside a cave. No one dared go near it until a young girl named Tara decided to find the truth. She climbed for hours through cold fog and sharp rocks. When she finally reached the cave, she found not a dragon but a beautiful waterfall hidden behind the stones.',
                'word_count': 62,
                'theme': 'fairy_tales'
            },
            {
                'title': 'The Dolphin Pod',
                'text': 'Off the coast of Kerala, a group of fishermen noticed something wonderful. A pod of dolphins was swimming alongside their boat, leaping in and out of the waves. The youngest dolphin seemed to be playing a game, splashing water at the boat with its tail. The fishermen watched in amazement as the dolphins raced ahead and then circled back.',
                'word_count': 62,
                'theme': 'animals'
            },
            {
                'title': 'The Satellite Launch',
                'text': 'The scientists at the space centre worked day and night to prepare the satellite for launch. Hundreds of tiny parts had to be tested and checked before it could fly into orbit. When the rocket finally lifted off the ground, the entire team cheered loudly. Their satellite would help farmers across India predict the weather more accurately.',
                'word_count': 60,
                'theme': 'space'
            }
        ],
        'GRADE_5': [
            {
                'title': 'The Secret Garden',
                'text': 'Mary stood before the high stone wall, searching for the hidden door she had read about in the old diary. Ivy covered the bricks like a thick, green blanket, hiding the entrance from curious eyes. Suddenly, a small robin landed on a branch and began to chirp loudly. It seemed to be pointing toward a brass handle buried deep beneath the leaves.',
                'word_count': 69,
                'theme': 'adventure'
            },
            {
                'title': 'The Mountain Trail',
                'text': 'The hiking group set out early in the morning when the air was still cool and fresh. As they climbed higher along the rocky trail, the view of the valley below became more breathtaking. Pine trees lined both sides of the narrow path and a gentle stream could be heard somewhere nearby. By noon, they reached the summit and sat down to enjoy their packed lunches.',
                'word_count': 66,
                'theme': 'adventure'
            },
            {
                'title': 'The Old Library',
                'text': 'Behind the town hall stood an old library that very few people visited anymore. Inside, the shelves were filled with dusty books that smelled of aged paper and adventure. One afternoon, Kavya discovered a handwritten journal tucked between two heavy encyclopedias. The journal belonged to a sailor who had traveled the world over a hundred years ago.',
                'word_count': 60,
                'theme': 'fairy_tales'
            },
            {
                'title': 'The Snow Leopard',
                'text': 'Deep in the mountains of Ladakh, a wildlife photographer waited silently behind a cold rock. She had been camping at this spot for five days hoping to catch a glimpse of the rare snow leopard. On the sixth morning, just as the first rays of sunlight hit the peaks, a graceful shape appeared on the ridge above her.',
                'word_count': 60,
                'theme': 'animals'
            },
            {
                'title': 'Journey to the Stars',
                'text': 'The International Space Station orbits the Earth sixteen times every single day, traveling at over twenty seven thousand kilometers per hour. Astronauts living on board conduct experiments in zero gravity that cannot be done anywhere on our planet. They watch the sunrise and sunset sixteen times daily through their small windows. Living in space changes how they see our world forever.',
                'word_count': 62,
                'theme': 'space'
            }
        ],
        'GRADE_6': [
            {
                'title': 'Ocean Depths',
                'text': 'Down in the deepest parts of the ocean, where sunlight never reaches, brilliant creatures create their own light. This bioluminescence allows them to find food and communicate in the sub-zero temperatures. Scientists use specialized robotic cameras to study these elusive animals, discovering species that look like they belong in a science fiction movie. The underwater world remains one of the greatest mysteries on Earth.',
                'word_count': 72,
                'theme': 'animals'
            },
            {
                'title': 'The Silk Road',
                'text': 'Centuries ago, merchants traveled thousands of miles along ancient trade routes connecting Asia to Europe. These paths, known collectively as the Silk Road, carried not only silk and spices but also ideas, languages, and inventions. Traders faced harsh deserts, towering mountain passes, and dangerous bandits along the way. Despite these challenges, the exchange of goods and culture shaped the modern world we know today.',
                'word_count': 68,
                'theme': 'adventure'
            },
            {
                'title': 'Solar Energy',
                'text': 'In many parts of India, villages that once had no electricity now use solar panels to power their homes and schools. These panels convert sunlight directly into electrical energy without producing any pollution. A single rooftop installation can provide enough power for lights, fans, and even a small refrigerator. This clean technology is helping millions of families improve their quality of life.',
                'word_count': 64,
                'theme': 'space'
            },
            {
                'title': 'The Curse of the Jade Necklace',
                'text': 'Legend has it that an ancient jade necklace was hidden in the ruins of a forgotten temple deep in the Western Ghats. Whoever wore it would gain the ability to speak with animals but would lose the power if they ever told a lie. Many adventurers had searched for the necklace over the centuries but none had returned with proof of its existence.',
                'word_count': 64,
                'theme': 'fairy_tales'
            },
            {
                'title': 'The Tiger Census',
                'text': 'Every four years, hundreds of forest officers and volunteers spread across the national parks of India to count the tiger population. They set up camera traps along animal trails and study paw prints left in soft mud. Each tiger has a unique pattern of stripes, much like human fingerprints. This careful work has helped increase tiger numbers significantly over the past two decades.',
                'word_count': 64,
                'theme': 'animals'
            }
        ],
        'GRADE_7': [
            {
                'title': 'The Inventions of Leonardo',
                'text': 'Leonardo da Vinci was a man far ahead of his time, filling his notebooks with sketches of flying machines and armored vehicles. Though many of his designs were never built during his lifetime, they reveal an extraordinary understanding of physics and engineering. His curiosity about the natural world drove him to study everything from the flow of water to the anatomy of the human body, bridging the gap between art and science.',
                'word_count': 78,
                'theme': 'adventure'
            },
            {
                'title': 'The Rainforest Ecosystem',
                'text': 'Tropical rainforests cover less than six percent of the Earth but are home to more than half of all known plant and animal species. The dense canopy blocks most sunlight from reaching the forest floor, creating layers of unique habitats at different heights. Indigenous communities have lived sustainably within these forests for thousands of years, understanding the delicate balance between taking from nature and giving back to it.',
                'word_count': 72,
                'theme': 'animals'
            },
            {
                'title': 'The Marathon Runner',
                'text': 'Deepa had never imagined she would run a marathon, but months of disciplined training had brought her to the starting line. The first twenty kilometers felt manageable, but beyond that her legs grew heavy and her breathing became labored. She focused on putting one foot in front of the other, remembering her coach\'s words about mental strength. When she finally crossed the finish line, tears of joy streamed down her face.',
                'word_count': 74,
                'theme': 'adventure'
            },
            {
                'title': 'Black Holes',
                'text': 'At the centre of nearly every galaxy lies an object so dense that not even light can escape its gravitational pull. These black holes warp the fabric of space and time in ways that challenge our understanding of physics. In two thousand nineteen, scientists captured the first ever photograph of a black hole, a blurry orange ring surrounding a dark shadow. That single image confirmed theories that physicists had debated for over a century.',
                'word_count': 76,
                'theme': 'space'
            },
            {
                'title': 'The Glass Mountain',
                'text': 'In the old stories of Eastern Europe, there was said to be a mountain made entirely of glass. At its peak sat a golden castle where a princess waited for someone brave enough to climb. Knights in armor slid back down every time they tried to scale the smooth surface. Only a clever young farmer, using nothing but sharp iron nails and bare determination, finally reached the top.',
                'word_count': 70,
                'theme': 'fairy_tales'
            }
        ],
        'GRADE_8': [
            {
                'title': 'Evolution of Technology',
                'text': 'The rapid advancement of artificial intelligence has fundamentally transformed how we interact with information and each other. While productivity has increased exponentially, these changes also bring forth complex ethical considerations regarding privacy and employment. It is essential for society to navigate this digital frontier with caution, ensuring that technology serves to enhance human potential rather than diminish it. As we look toward the future, the balance between innovation and responsibility will be more crucial than ever.',
                'word_count': 84,
                'theme': 'space'
            },
            {
                'title': 'Climate and Civilization',
                'text': 'Throughout history, changes in climate have profoundly influenced the rise and fall of civilizations. Prolonged droughts contributed to the decline of the Indus Valley civilization, while favorable monsoon patterns enabled the flourishing of agriculture across Southeast Asia. Modern scientists study ice cores and ocean sediments to reconstruct past climates, helping us understand patterns that could predict future environmental shifts. This knowledge is critical as humanity confronts the consequences of rapid global warming.',
                'word_count': 78,
                'theme': 'adventure'
            },
            {
                'title': 'The Power of Language',
                'text': 'India is home to over nineteen thousand languages and dialects, making it one of the most linguistically diverse nations on the planet. Each language carries within it centuries of cultural knowledge, unique expressions, and distinct ways of understanding the world. When a language disappears, an irreplaceable perspective is lost forever. Efforts to document and revitalize endangered languages have gained momentum, driven by communities who recognize that preserving their mother tongue means preserving their identity.',
                'word_count': 80,
                'theme': 'adventure'
            },
            {
                'title': 'The Migration of Monarchs',
                'text': 'Every autumn, millions of monarch butterflies embark on an extraordinary journey spanning over four thousand kilometers from Canada to the mountains of central Mexico. What makes this migration remarkable is that no single butterfly completes the entire round trip. Instead, it takes multiple generations, each instinctively knowing the exact route their great grandparents traveled. Scientists are still trying to fully understand the genetic compass that guides these fragile creatures across an entire continent.',
                'word_count': 78,
                'theme': 'animals'
            },
            {
                'title': 'The Library of Alexandria',
                'text': 'The Great Library of Alexandria was once the largest repository of knowledge in the ancient world, housing hundreds of thousands of scrolls from every corner of civilization. Scholars traveled from distant lands to study astronomy, mathematics, and philosophy within its walls. Its destruction, whether by fire, neglect, or conquest, remains one of history\'s most debated mysteries. The loss of so much accumulated wisdom reminds us how fragile the preservation of knowledge truly is.',
                'word_count': 78,
                'theme': 'fairy_tales'
            }
        ],
    },
    'HI': {
        'PRE_K': [
            {
                'title': 'छोटा चूहा',
                'text': 'एक छोटा चूहा था। वह बहुत खुश था। उसके पास एक सेब था। सेब लाल था।',
                'word_count': 15,
                'theme': 'animals'
            }
        ],
        'KINDERGARTEN': [
            {
                 'title': 'मेरा घर',
                 'text': 'यह मेरा घर है। मेरा घर बड़ा है। इसमें एक छोटा बगीचा भी है। मुझे मेरा घर पसंद है।',
                 'word_count': 20,
                 'theme': 'adventure'
            }
        ],
        'GRADE_1': [
            {
                'title': 'चालाक लोमड़ी',
                'text': 'एक जंगल में एक लोमड़ी रहती थी। वह बहुत चालाक थी। एक दिन उसे एक अंगूर का गुच्छा दिखा। उसने कोशिश की पर वह ऊपर था।',
                'word_count': 28,
                'theme': 'animals'
            }
        ]
    },
    'KN': {
        'PRE_K': [
            {
                'title': 'ಪುಟ್ಟ ಹಕ್ಕಿ',
                'text': 'ಒಂದು ಪುಟ್ಟ ಹಕ್ಕಿ ಇತ್ತು. ಅದು ಹಾರುತ್ತಿತ್ತು. ಅದಕ್ಕೆ ಹಸಿವಾಯಿತು. ಅದು ಹಣ್ಣನ್ನು ತಿಂದಿತು.',
                'word_count': 12,
                'theme': 'animals'
            }
        ],
        'KINDERGARTEN': [
            {
                 'title': 'ನನ್ನ ಶಾಲೆ',
                 'text': 'ನನ್ನ ಶಾಲೆ ತುಂಬಾ ಚೆನ್ನಾಗಿದೆ. ನಾನು ಪ್ರತಿದಿನ ಶಾಲೆಗೆ ಹೋಗುತ್ತೇನೆ. ಅಲ್ಲಿ ನನ್ನ ಗೆಳೆಯರಿದ್ದಾರೆ. ನಾವು ಒಟ್ಟಾಗಿ ಆಟವಾಡುತ್ತೇವೆ.',
                 'word_count': 18,
                 'theme': 'adventure'
            }
        ],
        'GRADE_1': [
            {
                'title': 'ಬಣ್ಣದ ಚಿಟ್ಟೆ',
                'text': 'ತೋಟದಲ್ಲಿ ಬಣ್ಣ ಬಣ್ಣದ ಚಿಟ್ಟೆಗಳು ಇದ್ದವು. ಒಂದು ಕೆಂಪು ಚಿಟ್ಟೆ ಹೂವಿನ ಮೇಲೆ ಕುಳಿತಿತ್ತು. ನಾನು ಅದನ್ನು ಹಿಡಿಯಲು ಹೋದೆ, ಅದು ಹಾರಿಹೋಯಿತು.',
                'word_count': 25,
                'theme': 'animals'
            }
        ]
    }
}

def _db_passage_to_dict(passage):
    """Convert a ReadingPassage model instance to the dict format used by templates."""
    return {
        'title': passage.title,
        'text': passage.text,
        'word_count': passage.word_count,
        'theme': passage.theme,
    }


def _get_from_db(grade, lang, theme, passage_idx):
    """Try to get a passage from the database. Returns dict or None."""
    try:
        from apps.portal.models import ReadingPassage
        qs = ReadingPassage.objects.filter(grade=grade, language=lang, is_active=True)
        if theme:
            themed_qs = qs.filter(theme=theme)
            if themed_qs.exists():
                qs = themed_qs
        if not qs.exists():
            return None
        passages = list(qs)
        idx = passage_idx % len(passages)
        return _db_passage_to_dict(passages[idx])
    except Exception:
        return None


def _get_from_static(grade, lang, theme, passage_idx):
    """Fallback: get passage from the static READING_PASSAGES dict."""
    lang_passages = READING_PASSAGES.get(lang, READING_PASSAGES['EN'])

    target_grade = grade
    if target_grade not in lang_passages:
        grades_priority = ['PRE_K', 'KINDERGARTEN', 'GRADE_1', 'GRADE_2', 'GRADE_3', 'GRADE_4', 'GRADE_5', 'GRADE_6', 'GRADE_7', 'GRADE_8']
        try:
            current_idx = grades_priority.index(grade)
            for i in range(current_idx - 1, -1, -1):
                prev_grade = grades_priority[i]
                if prev_grade in lang_passages:
                    target_grade = prev_grade
                    break
            else:
                target_grade = 'PRE_K'
        except ValueError:
            target_grade = 'PRE_K'

    passages_list = lang_passages.get(target_grade, lang_passages['PRE_K'])
    if not isinstance(passages_list, list):
        return passages_list

    if theme:
        themed = [p for p in passages_list if p.get('theme') == theme]
        if themed:
            passages_list = themed

    idx = passage_idx % len(passages_list)
    return passages_list[idx]


def get_passage_for_grade(grade, lang='EN', passage_idx=0, theme=None):
    """Get a reading passage. Tries DB first, falls back to static dict."""
    result = _get_from_db(grade, lang, theme, passage_idx)
    if result:
        return result
    return _get_from_static(grade, lang, theme, passage_idx)
