from src.interfaces.content_splitter import Section
from src.repositories.ml.bert_summary import SectionSummarizer
from src.settings import Settings


def test_bert_summary():

    # Test the summarize method with a sample text
    sample_text = """
    Les débuts
Issu d’une famille de courtiers en vins du Languedoc, après des études à Brignac, au Petit séminaire de Carcassonne et à Montpellier, le jeune Louis manifeste rapidement son goût pour la littérature. Il écrit de nombreuses pièces, drames ou vaudevilles, et publie des poèmes dans la presse locale où il est aussi revistero pour l'hebdomadaire Le Torero[2]. Il écrit un feuilleton inachevé, Mémoires d'un toréador français, publié posthumément en volume[3].

En 1898, au décès de ses parents, il laisse l'affaire familiale aux mains de ses frères et il part à Paris où il débute comme journaliste au quotidien La Croix. Amateur de tauromachie, il fonde avec Étienne Arnaud le « Toro-Club parisien » où il fait la connaissance d'André Heuzé, auteur dramatique, scénariste et amateur de tauromachie lui aussi. C'est par ce dernier que Feuillade entre en contact avec le cinéma[4].

En septembre 1903, il fonde un hebdomadaire satirique, La Tomate, dont l'existence ne dépasse pas trois mois. Il collabore ensuite au Soleil (1904), quotidien de tendance monarchiste, puis à la Revue mondiale comme secrétaire de rédaction. Il parvient à faire jouer quelques pièces de théâtre, comme Le Clos, acte en vers présenté à Béziers en 1905 et dont il est coauteur. La même année il présente quelques scénarios chez Gaumont, société originellement tournée vers la photographie, mais qui développe des ambitions cinématographiques.

Il fait la connaissance d’Alice Guy, la première femme réalisatrice de l'histoire du cinéma, dont il devient le scénariste attitré.

En 1906, il coréalise, avec sa protectrice, quelques petits films aujourd’hui perdus. Il devient ensuite entièrement responsable de ses films (dont il écrit toujours les scénarios, à quelques rares exceptions près). Son premier film personnel à ce jour[Quand ?] identifié est comique : C'est papa qui prend la purge (1907).

En 1907, Alice Guy doit suivre son époux Herbert Blaché nommé responsable de la succursale de Gaumont à Berlin, et suggère à Léon Gaumont de nommer Feuillade au poste de directeur artistique. À partir du 1er avril 1907, le voici donc responsable des choix artistiques d'une compagnie cinématographique française dont l'ambition est de concurrencer la maison Pathé.

Travailleur acharné, il réalise en vingt ans environ huit cents courts et moyens métrages dont plus des deux tiers ont aujourd’hui disparu. Il filme avec la rigueur documentaire des frères Lumière et la fantaisie de Georges Méliès dont il devient le grand rival. Il aborde tous les genres : le burlesque, les mélodrames, le fantastique humoristique, l’anticipation, les films historiques et même des « péplums » qui traitent de la mythologie, de l’histoire sainte ou de l’époque romaine.

En 1906, il souffle à Alice Guy des idées de courts métrages tauromachiques : Courses de taureaux à Nîmes, Passes du toreador Machaquito[5], tournés dans l'amphithéâtre nîmois.

En 1908, il réalise dans la Cité de Carcassonne une série de films moyenâgeux dont il ne subsiste que des cartes postales dues au photographe Michel Jordy, représentant des scènes de tournage. Il s'agit d'un des premiers tournages de films muets réalisés en extérieur[6].

En 1910, Louis Feuillade est l’un des inventeurs du feuilleton au cinéma avec sa série sur Bébé, joué par le jeune René Dary tout juste âgé de cinq ans et qui tourne en trois ans près de 70 films. Suit, à partir de 1913, une autre série avec un enfant, Bout de Zan interprété par René Poyen.

Entretemps, en 1910, pour contrebalancer Le Film d'art (l'Assassinat du Duc de Guise), Louis Feuillade promeut la série Gaumont "Le Film esthétique", pour laquelle il met en scène des œuvres religieuses, Pater, Les Sept Péchés capitaux, La Nativité, La Vierge d'Argos et des histoires inspirées de la civilisation gréco-romaine[7]. Cette tentative n'eut pas le succès escompté et fut interrompue dès l'année suivante. Feuillade entreprend alors La Vie telle qu'elle est, nouvelle série de films supposés montrer des « scènes de la vie réelles », concurrençant la série de ce nom de la Vitagraph. Enfin, une autre série, La Vie drôle, basée sur les thèmes du vaudeville, est filmée en 1913 et 1914.

En 1914, il se rend en Espagne pour réaliser deux fictions illustrant le thème taurin : Les Fiancés de Séville où un torero jaloux du peintre qui fait le portrait de sa fiancée lui donne un coup de poignard avant de se suicider dans l'arène[5]. La déclaration de la guerre ne lui permet pas d'achever son deuxième film espagnol, mais une des séquences tournées à ce moment-là sera intégrée au sixième épisode des Vampires qui porte le titre Les Yeux qui fascinent (1916)[5].

Les séries

Fantômas s'apprête à compromettre le peintre Jacques Dollon dans l'assassinat de la baronne de Vibray (Le Mort qui tue, 1913).
En 1913, Louis Feuillade adapte sur grand écran le roman de Marcel Allain et Pierre Souvestre Fantômas avec René Navarre métamorphosé en empereur du crime tandis que Georges Melchior est le journaliste Fandor et Edmond Bréon, l’inspecteur Juve. Les spectateurs frémissent et en redemandent toujours plus. Le succès est phénoménal. Cinq épisodes sont réalisés : Fantômas, Juve Contre Fantômas, Le Mort qui tue, Fantômas contre Fantômas et Le Faux Magistrat.

La guerre surprend Feuillade en plein tournage. Les techniciens et artistes en âge de l'être, comme René Navarre, sont appelés sous les drapeaux. Les autorisations de projections cinématographiques se font rares. Pourtant, au début de l'année 1915, sur les instances de son patron, Feuillade reprend ses caméras et réalise quelques drames patriotiques (Deux Françaises, Union sacrée) avant de se voir appelé à son tour. Réformé en juillet 1915 pour troubles cardiaques, il reprend aussitôt ses fonctions au sein de la maison Gaumont.


Irma Vep (Musidora) se dévoile devant la bande des Vampires sur la scène du cabaret le « Chat-Huant »
(Les Vampires, épisode « Le Maître de la foudre », 1915).
Pathé annonce la présentation française du film à épisodes Les Mystères de New York (The Exploits of Elaine) présenté sous forme de ciné-roman : le public lisait le feuilleton dans la presse avant d'aller voir le film en salles. La réponse de Gaumont est Les Vampires. Il fallait une actrice capable de rivaliser avec Pearl White : Musidora, qui travaille avec Feuillade depuis l'année précédente (Severo Torelli) est Irma Vep, l’égérie de la mystérieuses bande des « Vampires », séduisante et troublante incarnation des forces du mal. L'acteur principal, Édouard Mathé, a remplacé Navarre au sein de l'équipe. Dans le rôle du reporter Philippe Guérande, il lutte, non sans mal, contre ces forces obscures, avec l’aide d’un « vampire » repenti, Mazamette, incarné par le comique Marcel Lévesque. La série comprend 10 films présentés sur autant de semaines consécutives.

Le préfet de police de Paris — le vrai —, agacé de voir sa police ridiculisée, fait interdire un temps les projections publiques du film. Porté aux nues par les surréalistes, Les Vampires reste comme l'apogée de la carrière de Feuillade.

Plus conforme à la morale bourgeoise, Judex, ciné-roman en 12 épisodes présentés fin 1916, valorise davantage le héros positif. Interprétés par René Cresté et Musidora, les protagonistes, Judex et Diana Monti, se disputent, pour des causes opposées, la fortune d'un banquier véreux. La suite sortie l’année suivante, La Nouvelle Mission de Judex, est généralement considérée comme moins réussie.

Moins connus mais plus esthétiques, les douze épisodes de Tih Minh (1919) avec l’exotique Mary Harald, actrice britannique née à Hong-Kong et ceux de Barrabas[8] (1919), avec le vétéran Gaston Michel dans le rôle du maître du crime et où Georges Biscot prend la relève de Marcel Lévesque dans le registre comique.

Dans Vendémiaire (1919), hymne à la vigne source de vie, retour aux origines héraultaises, Louis Feuillade met en scène un officier devenu aveugle à la suite d’une blessure au combat et qui accueille dans sa propriété des réfugiés chassés par le conflit de la Première Guerre Mondiale.

Les années 1920

Louis Feuillade en 1923 (photographie agence Rol).
Avec le retour de la paix, la décence et la moralité sont à l’ordre du jour, et pour Feuillade les séries de la nouvelle décennie penchent nettement du côté du mélodrame. À partir des Deux Gamines (1921), le crime triomphant cède le pas à l’innocence persécutée. Le roman familial, jusqu’alors sous-jacent dans ses films à épisodes de Feuillade, passe maintenant au premier plan. À sa troupe habituelle de comédiens le metteur en scène a adjoint la danseuse Sandra Milowanoff, venant des ballets russes de Serge de Diaghilev. Le film, immédiatement, lui apporte la gloire. Les Deux Gamines, présenté au Gaumont-Palace de janvier à avril 1921, est plébiscité par le public. Les films à épisodes suivants de Feuillade seront toujours accueillis par le public avec la plus grande faveur. Mais il ne retrouve jamais un tel triomphe.

Entre deux ciné-romans, l’infatigable Feuillade met en scène, toujours avec Biscot, les cinq vaudevilles de la série Belle Humeur, entre 1921 et 1922. Si le comique n’est pas toujours d’une grande légèreté, il est toujours d’une réelle efficacité et le ton de l’ensemble de la série ne dément pas son titre. Dans les deux serials suivants, L'Orpheline (1908) et Parisette (1922), on retrouve Sandra Milowanoff, mais aussi un jeune premier nommé René Clair.

Le Fils du Flibustier (1922), son dernier ciné-roman en 12 épisodes, est davantage tourné vers l'aventure et donne l'occasion à Aimé Simon-Girard, fraîchement auréolé de son succès dans Les Trois Mousquetaires (1921) de Henri Diamant-Berger, de recomposer un personnage virevoltant et batailleur dans une œuvre où réalité et imagination se mélangent habilement

En 1923, la mode du film à épisodes commence à s’essouffler. Vindicta, dont l’action se déroule au XVIIIe siècle en Provence et aux Îles, ne comporte que cinq « périodes ».

Une gamine de six ans, Bouboule, remarquée d’abord par Mistinguett, se révèle, devant la caméra de Feuillade, une véritable bête de cinéma, d’une stupéfiante spontanéité. Dès sa première apparition dans Le Gamin de Paris, sorti fin 1923, le public n’a d’yeux que pour elle. Elle ne tient pourtant qu’un rôle modeste dans ce film dont Sandra Milowanoff et René Poyen, ex-Bout-de-Zan devenu adolescent, sont les personnages principaux.

Feuillade consacre l’année 1924 tout entière à sa jeune vedette dont René Poyen est le partenaire régulier. Après La Gosseline, La Fille bien gardée, il les met en scène dans un feuilleton en six épisodes, L'Orphelin de Paris. Les deux meilleurs films du jeune tandem sont cependant Pierrot, Pierrette et Lucette, dans lesquels ils se montrent l’un et l’autre bouleversants.

Épuisé par une vie de travail ininterrompu, contraint à un repos complet durant l'été 1924, Louis Feuillade réalise ses deux derniers films avec l'aide de son gendre, Maurice Champreux. Il meurt à 52 ans, le 26 février 1925, à Nice, des suites d'une péritonite, quelques jours à peine après avoir achevé Le Stigmate. Il est inhumé au cimetière Saint-Gérard de Lunel.
    """
    section = Section(title="Test Section", content=sample_text)

    summarize = SectionSummarizer(Settings())

    # when
    section = summarize.process(section)

    assert section is not None
    assert section.title == "Test Section"
    assert len(section.content) <= len(sample_text)
