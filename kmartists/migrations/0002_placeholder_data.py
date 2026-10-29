from datetime import UTC, datetime
from uuid import uuid4

from django.db import migrations

USERS = [
    {
        "name": "guest",
        "looking_for_band": False,
        "location": "",
        "instruments": [],
        "favorite_bands": [],
    },
    {
        "name": "bassline_bohdan",
        "looking_for_band": True,
        "location": "Kyiv",
        "instruments": ["bass guitar"],
        "favorite_bands": ["Rush", "Primus"],
    },
    {
        "name": "drumroll_daria",
        "looking_for_band": True,
        "location": "Lviv",
        "instruments": ["drums", "percussion"],
        "favorite_bands": ["Tool"],
    },
    {
        "name": "vinyl_vira",
        "looking_for_band": False,
        "location": "Kharkiv",
        "instruments": ["keyboards"],
        "favorite_bands": ["Radiohead"],
    },
    {
        "name": "Viktor_Drumdemon",
        "looking_for_band": False,
        "location": "",
        "instruments": ["drums"],
        "favorite_bands": ["Leaf's Moshin"],
    },
]

EVENTS = [
    {
        "creator": "bassline_bohdan",
        "name": "Kyiv Basement Jam",
        "date": datetime(2027, 3, 12, 19, 0, tzinfo=UTC),
        "location": "Kyiv",
        "description": "Open jam session for bassists, drummers and anyone who can keep a groove.",
        "contact_info": "bohdan@kmartists.example",
    },
    {
        "creator": "drumroll_daria",
        "name": "Lviv Percussion Night",
        "date": datetime(2027, 4, 2, 20, 0, tzinfo=UTC),
        "location": "Lviv",
        "description": "An evening of drum circles and percussion workshops.",
        "contact_info": "daria@kmartists.example",
    },
    {
        "creator": "vinyl_vira",
        "name": "Kharkiv Vinyl Swap",
        "date": datetime(2027, 5, 16, 15, 0, tzinfo=UTC),
        "location": "Kharkiv",
        "description": "Bring your records, trade with fellow collectors, listen to rare pressings.",
        "contact_info": "vira@kmartists.example",
    },
]

ARTICLES = [
    {
        "artist": "DakhaBrakha",
        "genres": ["folk", "world"],
        "body": [
            {"title": "Overview", "content": "Kyiv quartet blending Ukrainian folk with rhythms from around the world."},
            {"title": "Sound", "content": "Built around cello, accordion, percussion and layered vocal harmonies."},
        ],
        "contributors": ["vinyl_vira", "bassline_bohdan"],
    },
    {
        "artist": "Jinjer",
        "genres": ["metalcore", "progressive metal"],
        "body": [
            {"title": "Overview", "content": "Progressive metal band formed in Donetsk Oblast."},
            {"title": "Sound", "content": "Known for shifting between clean and harsh vocals over complex rhythms."},
        ],
        "contributors": ["drumroll_daria"],
    },
    {
        "artist": "Okean Elzy",
        "genres": ["rock", "pop rock"],
        "body": [
            {"title": "Overview", "content": "Rock band from Lviv and one of the best-known Ukrainian groups."},
        ],
        "contributors": ["bassline_bohdan"],
    },
    {
        "artist": "Leaf's Moshin",
        "genres": ["hip hop", "rap"],
        "body": [
            {
                "title": "Overview",
                "content": "Ukrainian rapper based in Kyiv who releases music on SoundCloud, Spotify and YouTube,"
                "with track titles written in Ukrainian.",
            },
            {
                "title": "Releases",
                "content": "MOSHPIT (August 2025); мене не врятуєш (freestyle) (September 2025); "
                "чуже життя (November 2025); ти така гарна (December 2025); "
                "вибач мені, що не буду поруч тут (freestyle) (January 2026); тенети (February 2026); "
                "мої бро таланти (March 2026); небо (June 2026); waterfall (July 2026); "
                "наливаю у стакан (September 2026).",
            },
            {
                "title": "Producers",
                "content": "Credited producers include 6astard (тенети), eeryskies "
                "(вибач мені, що не буду поруч тут) and rollie (мене не врятуєш). "
                "чуже життя is credited as \"prod. for Izumi\".",
            },
            {
                "title": "Links",
                "content": "SoundCloud: https://soundcloud.com/leafsmoshinmusic; Telegram channel: @leafs_moshin.",
            },
        ],
        "contributors": ["Viktor_Drumdemon"],
    },
]


def create_placeholders(apps, schema_editor):
    User = apps.get_model("kmartists", "User")
    Event = apps.get_model("kmartists", "Event")
    Article = apps.get_model("kmartists", "Article")

    users = {user.name: user for user in User.objects.bulk_create(User(id=uuid4(), **user) for user in USERS)}
    Event.objects.bulk_create(
        Event(**{**event, "id": uuid4(), "creator": users[event["creator"]]}) for event in EVENTS
    )
    for article in ARTICLES:
        record = Article.objects.create(
            id=uuid4(), artist=article["artist"], genres=article["genres"], body=article["body"]
        )
        record.contributors.set(users[name] for name in article["contributors"])


def remove_placeholders(apps, schema_editor):
    apps.get_model("kmartists", "Article").objects.filter(artist__in=[article["artist"] for article in ARTICLES]).delete()
    apps.get_model("kmartists", "Event").objects.filter(name__in=[event["name"] for event in EVENTS]).delete()
    apps.get_model("kmartists", "User").objects.filter(name__in=[user["name"] for user in USERS]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("kmartists", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_placeholders, remove_placeholders),
    ]
