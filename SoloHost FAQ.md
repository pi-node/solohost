# Node & SoloHost FAQ

## Can I run Node on one machine and SoloHost on another?

Yes, but Node rewards are only counted for the main account, and there is no need to run the blockchain on the second machine.

However, a single Node ID cannot be associated with two different users.

If you are running SoloHost on both machines, note that SoloHost Remote can only be paired with one device at a time. Entering the one-time code on a second device disconnects the previous one automatically.

## Do I need Soroban to run SoloHost?

No. Soroban is only a service for developing and using smart contracts, so it is useful if you need its API (e.g. when developing smart contracts). If you do not use smart contracts, there is no benefit to enabling it. The same applies to Horizon, the additional blockchain API.

## Can I use Pi Desktop on more than one device?

Yes, but only run the blockchain on the main account.

## Each Node ID may only be associated with 1 unique user account. Does this rule apply to SoloHost?

For Node, one Node can only be associated with one user, but one user can have multiple Nodes.

SoloHost does not have an equivalent rule. What applies to SoloHost instead is a sign-in limit and app usage tracking.

**Sign-in limit.** Your Pi account can be signed in to SoloHost on up to 10 machines at once. If you reach that limit, the oldest sign-in is dropped and that machine can simply sign in again. Nothing is blocked or flagged when this happens, and most users will never run into it.

**App usage tracking.** As of version 0.6.3, SoloHost tracks app usage. Tracking starts only after you sign in, and it covers which apps are running, not app content. This data powers the app ranking, since apps are ranked by how many people are currently running them.
