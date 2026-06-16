
PLEASE LET ME INTO ISEF BRUH
- vibecoded because i SUCK

fire update log im starting bc this shit is starting to get confusing
DD/MM/YY

14/6/2026 11:53PM 
- waypoint pathfinding FIXED, node graph will always have a solution/viable pathway 100% of the time. waypoint/head will always spawn atop the electromagnet with the most nanoparticles
- however, agent/head cannot dictate the strength of electromagnets yet, yielding like a 0% success rate, but ill fix that in a sec. the decider that picks where the waypoint will spawn must ignore the nanoparticles already in zone, or i could make them disappear/get collected when they touch zone or something. but im not sure how that will work irl....
- will add more heads later
- drank a really good mocha

15/6/2026 10:57PM
- v1 is basically completed, waypoints can now dictate electromagnets and successfully guide at least 60% of the nanoparticles into the target zone
- waypoint pathfinding basically is perfect, i may switch to dijkstra instead of a* because its not taking the most efficient path sometimes (least nodes v least distance)
- there are occasions where it gets stuck, due to the electromagnets being not precise enough (theyre too big), causing the nanoparticles to get stuck on walls
- waypoint also always spawns on the node closest to the middle of the electromagnet, causing failure loops if the nanoparticles get stuck (idk really how to explain it here)
- it is almost time to buy parts soon!
- no hemodynamix yet cuz the vascular genny is not closed loop :( ill just build a pump irl i guess
