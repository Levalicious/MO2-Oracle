# PoC

This plugin is NOT READY FOR SERIOUS USAGE.

At the moment it deliberately does not automatically save its state; however you can save it by clicking `Oracle > Save`. Note that saving state will NOT affect how much time this plugin takes to run.

At some point I need to integrate the functionality from the sync_plugins plugin to make the plugin load order match the mod load order upon order changes.

This plugin is SLOW. We ID mods by file content, not by mod name, as transferring of probabilities in that sense needs to be explicit, not automatic. Mod updates can and do break other mods, and mods are often compatible up to some degree of version parity. 

The IDs are calculated by taking directory hashes of the contents of each mod. We restrict to active mods, but if you're like me and have > 200 active mods, that hashing is still going to be slow. This slowdown _should_ occur at MO2 startup, and may make your MO2 instance hang for a minute while it processes. Don't worry about it, and if windows prompts you about MO2 not responding, just hit "wait".

The slowness _is_ an issue, and I will be working on it, but considering that over the course of today I got it from "adding > 20 minutes to MO2's startup time" down to "eh bout 3 minutes" I'm taking that as a win. 


## What It Does

### Training:
This plugin is not LOOT. It does not come with a database of known relations. That's for future work, and so is the ability to integrate that information. As such, this plugin needs to be trained. It maintains a set of probability distributions, and on each game run it will check the exit code provided by MO2. If it's a crash, that'll be recorded, and if the game exits successfully the plugin will prompt you for a confirmation that the load order worked as intended. 

Feel free to be as iffy or strict as you like here. Is one irrelevant texture wrong but the game otherwise runs perfectly fine? Mark it okay! Is that one texture _really_ bothering you? Mark it as failed! If the search process gives you that load order again, you can reevaluate later. If not, it should move you to an improved & more stable load order.

Remember, this plugin does not save state automatically. If you want to save the training data you've painstakingly built up, make sure to hit `Oracle > Save` frequently, or you'll be left with nothing but a long MO2 startup time.

### `Oracle > Predict`

Predict gives an estimate for the likelihood of the current load order causing a crash. It also gives entropy values in the range of 0.0 - 1.0 to estimate its uncertainty about the order. As mentioned above, without training this plugin will have _no idea_ what is or isn't a good order and will give high crash likelihoods for everything. You should, however, be able to see the accompanying entropy value will be 1.0 or some other high value, indicating that it has no idea what the shit it's doing.

Give it a few runs. It'll learn.

### `Oracle > Sample Optimal`

The bread and butter. Click this, and (again, given training) the plugin will generate a load order for you to use. It uses a modified form of Zermelo's algorithm from [this paper](https://jmlr.org/papers/volume24/22-1086/22-1086.pdf) and generates the load order least likely to crash.

Is my usage incoherent? yes. Is it better than my previous approaches? yes. Does it seem to be working? yes. Is my best guess that the differences in this application of it make the problem nonconvex and the algorithm incapable of providing the global optimum? yes. Does it matter? 

Actually maybe not! It would, in theory, if we were _just_ using this. But luckily, when the sampler generates bad load orders and then experiences them being bad, the sampling distributions get updated to reflect that. So, eh. It'll work until it doesn't, and then we'll swap it out with something new.

As an initial test for this plugin, install it and give A COPY OF your default load order a run. On exit, click the prompt to confirm that it worked, and go ahead and mess up your order a bit. Click this button, and watch it magically "heal". If it doesn't, send me a ping because I fucked up. Just make sure it has at least 1 run of training data.

### `Oracle > Sample InfoGain`

Generates a load order, like above. However, here the goal isn't to generate the "best" load order - the goal is to generate the most uncertain one. The sampler will, using the same approach as with the "optimal" order sampler, attempt to find the load order that will be most informative when tested. 

The idea is that we'll deliberately choose the highest-entropy load order we can find, run it, and then repeat; by deliberately focusing our learning on the least certain spots, we'll be picking the best load orders to minimize our model's overall uncertainty.

This sampler isn't _trying_ to deliberately generate orders that crash, but it almost definitely will do so every time. Consider, for a second, that without ordering information like dependencies, for N mods there are N! possible load orders, all of which would need to be tested because their relationships are a) highly correlated b) sufficiently higher order.

It's not a tenable search space, so we don't try to search the space and sample instead, but that's still a lot of uncertainty we simply can't eliminate (except with dependency information! but that's for later).

# BACK UP YOUR LOAD ORDER (PLUGIN AND MOD) BEFORE TRYING THIS
# BACK UP YOUR LOAD ORDER (PLUGIN AND MOD) BEFORE TRYING THIS
# BACK UP YOUR LOAD ORDER (PLUGIN AND MOD) BEFORE TRYING THIS

okay, I tried. I take no responsibility if you ignored the above and I messed up your mods.


### Future Plans

This learns, which is half the journey, but I have 2 major goals for this plugin.

1. Proper dependency handling

Most mods on Nexus and elsewhere have occasionally fairly deep dependency chains. These _significantly_ constrain load order. Not always, but often, and that is extremely useful here. I mentioned above that with N mods we have N! load orders to try. Even when N is 5, decreasing it by 1 makes a _big_ difference:

5! = 120 load orders

4! = 24 load orders

At higher mod counts this only gets worse. Even a really bad database of explicit dependencies missing entries for 80% of mods would have a huge effect on the amount of learning this plugin needs to do. Plus, this data _is_ available, even if it's a pain to access at times. Nexus has dependencies, although it needs better distinguishing for optional vs required ones. Mods often mark required masters. LOOT exists. Point is, data exists and is available, it just needs to get integrated and used.

2. Collaborative learning

The distributions being learnt here are not mod version or mod instance agnostic. If one of your mods hashes to a certain value, and the same hash shows up on someone else's computer, unless you two just broke SHA-256. Of course, if you have over 57 mods, 58! > 2^256, so at that point it's just a matter of global computational power, not lack of trying.

Still, the point is that if a relation between 2 mods gets updated by one user running tests, and the same relation gets updated by another user on their local machine, those two distributions can be aggregated into one.

I can only put in so many hours of Skyrim per hour (1, to be exact), but The People(tm) can achieve many times that. Aggregate all the tests.

This still needs some work: the storage handling is bad; we need a versioning or logical clock system so we don't double count updates; MO2 instances need to communicate with some central server or directly with eachother; the sampling distribution isn't great at understanding the concept of "I'm missing a mod"; aggregate databases would get chonky fast and sharding them would be nice; I'd like to make sure that this information can be shared in a privacy-preserving/anonymous way. No need for us to leak exactly [_which_ SoS mods](https://www.reddit.com/r/skyrimmods/comments/ttg2m8/odd_question_but_what_are_all_the_mods_that_have/) people have in their load orders.

There's work to be done yet, basically.

Other things this could potentially use:
- probabilistic bisection
  - probably best after proper dependency tracking
- Alternative sampling strategy
  - I abandoned gibbs but maybe that's more coherent here? Anyone who actually knows math let me know, because I have no idea what I'm doing
- ??????
- Making it not crash MO2 on a semi regular basis
- ??????

Still, with all that I think this could be pretty cool It's not really using any new ML ideas, just old ones in a context I was very surprised to never see them applied before.

What is, in my opinion, the most attractive feature here: it's (relatively) case agnostic. This is implemented with Skyrim Special Edition in mind, but that's just the interface - one should be able to apply this exact approach (possibly even a shared global database!) to mods from any game, whether it be Fallout or Minecraft. On that note, scratch the shared global database - Now we'll have permanently blank relations between Sounds of Skyrim and Buildcraft that some poor chump will have to store.
