# Chess-Bakery
Python code to run chess games over a serial connection on two Raspberry Pi computers.

There's too many hand-waving stats proving one chess engine is "stronger" than another.  Chess engine strengths are usually
simulated with calculations intended to show the relative strengths of engines with an ELO style number.  There are groups
who do engine-vs-engine competitions, but they run these competitions on a single computer, with the engines competing for
operating system resources, using a scaling factor to scale engine performance to some computer from the early 2000s.

There's nothing necessarily wrong with these processes;  chess engines are now so powerful that they can't be compared to human
players anymore, only to themselves.  My complaint comes from each and every chess engine webpage claiming that their chess
engine is arbitrarily stronger than other chess engines using some metric or another.  It's either that, or the author being
self-deprecating that the code isn't **intended** to be a good player, and just walking away.

## A scientific computer chess tournament

In order to actually rank chess engines fairly, it's important that each chess engine be able to use it's abilities to the fullest,
including pondering and any other time management tricks it may attempt to use to play strongly.  It should run on the exact same
hardware as it's competitor engine, with the exact same performance as it's competitor.  It should have the same hardware strengths
and limitations.  Whenever possible, the engine should be compiled specifically for that hardware platform, so that the engine
can take advantage of all the abilities of the platform whenever possible.

And most importnatly, the games should be **reproducible**.  This should be as scientific as possible.  By having reproducible
hardware, reproducible software, and reproducible methods, we should have a standardized process for comparing chess engines.

And I want to compare 'em all.  Strong engines.  Weak engines.  Experimental engines.  Monkey engines.  The human variety of
chess contains players from ELO 10 to ELO 2800, we should do the same for computer chess engines.

Currently, we only have a basic script which pitches two chess engines in a match of chess, with no configuration.  If you have
suggestions please open an issue.  Feel free to submit a pull request to make things better.
