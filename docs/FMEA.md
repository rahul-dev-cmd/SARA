# SARA - Design FMEA (planned fail-safes, not yet tested)

| Failure mode | Hazard | Fail-safe / mitigation |
|---|---|---|
| Signal loss (data link down > about 0.5 s) | SARA stuck deep in rubble | ESP32 watchdog cuts motor enable; head LEDs blink; operator pulls back with the retrieval line |
| Total electronics / power failure | No control, no video | Retrieval line is mechanical and needs no power; operator reels SARA in by hand |
| Retrieval line anchor failure | Line pulls out, SARA lost | Al eyebolt + backing plate (in CAD). Load still passes through the printed rear wall: pull-test planned |
| Tether / line snags on rubble | Cannot advance or retreat, cable damaged | Abrasion sleeve, line kept lightly taut, straight reverse pull, limited pull force |
| Battery over-temperature or short | Cell damage / fire | 2S BMS, fuse, 2 NTC sensors read by ESP32. Cutoff temperature set during bench tests (planned) |
| Belt jam / motor stall | Motor or driver overheating | TB6612 thermal shutdown, timed drive commands. No current sensing yet |
| Tendon cable breaks or slack | Joint goes limp, steering lost | 4 steel cables per joint share load; body can still be pulled out by the line |
| ESP32 runs out of pins | Wiring cannot be completed | Add a second I/O chip if needed |

No IP rating is claimed: the body is not sealed.
