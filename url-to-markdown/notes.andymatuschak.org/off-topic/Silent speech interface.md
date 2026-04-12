---
title: "Silent speech interface"
source: "https://notes.andymatuschak.org/zFNrLkCqVyTK22wRfDKDsqy"
captured: "2026-04-11T20:52:20Z"
---
# Silent speech interface

(see also [my survey article](https://www.patreon.com/posts/prospects-for-69855805) on this subject)

Silent speech interfaces attempt to discern speech without any (or with very little) audible utterance. They’re a form of [[Voice-based interface]].

I’m excited about these systems as a possible poor man’s [[Brain-computer interface]]. In the ideal case, they’d allow pervasive, unobtrusive command and textual input, and even a slow form of synthetic telepathy. More practically, they’re perhaps a way to resolve [[Reading texts on computers is unpleasant]] by bringing elements of the [[Dynamic medium]] to physical books.

A huge variety of sensing modalities are possible here, all with different trade-offs, broadly focusing on:

- cortical and nervous system signals (EEG, iEEG)
- motor neuron signals (surface EMG)
- motion of lips, face, jaw, vocal tract (ultrasound, video, radar, Doppler, strain gauges, magnetic implants, etc)
- acoustics (special microphones for whispers / murmurs)

Many of these approaches are invasive or highly obtrusive with current and foreseen sensors, and I’m interested in consumer scenarios, so I’ll focus on non-invasive and relatively non-obtrusive approaches.

The best routes I’ve seen seem to be (as of 2022 / 2024):

- [[Visual speech recognition]] (i.e. from video of the lips or face). Only cheap, widely-available equipment needed (some systems use RGB-D cameras).
	- For fixed-position scenarios, like one’s office or living room, this could be implemented without much disruption, though preparation of the environment may be a barrier. And one couldn’t move about the room freely.
		- This limitation could perhaps be improved by methods like those in [[Elgharib, M., Mendiratta, M., Thies, J., Niessner, M., Seidel, H.-P., Tewari, A., Golyanik, V., & Theobalt, C. (2020). Egocentric videoconferencing. ACM Transactions on Graphics, 39(6), 1–16]].
		- Processing pipelines are currently quite compute-intensive, not yet suitable for real-time applications.
		- State of the art:
		- Wang, X., Su, Z., Rekimoto, J., & Zhang, Y. (2024). Watch Your Mouth: Silent Speech Recognition with Depth Sensing. Proceedings of the CHI Conference on Human Factors in Computing Systems, 1–15. [https://doi.org/10.1145/3613904.3642092](https://doi.org/10.1145/3613904.3642092)
- Sub-audible acoustic recognition
	- One promising implementation uses a microphone held at the lips and “ingressive”, non-voiced speech: [[Fukumoto, M. (2018). SilentVoice: Unnoticeable Voice Input by Ingressive Speech. Proceedings of the 31st Annual ACM Symposium on User Interface Software and Technology, 237–246]]
		- perhaps [[Augmental]] could go this route via a dental retainer?
		- Whispering:
		- Hiraki, H., & Rekimoto, J. (2022). SilentWhisper: Faint whisper speech using wearable microphone. The Adjunct Publication of the 35th Annual ACM Symposium on User Interface Software and Technology, 1–3. [https://doi.org/10.1145/3526114.3558715](https://doi.org/10.1145/3526114.3558715)
		- Other approaches use surface-mounted microphones (“non-audible murmur” microphones), but the citation tree suggests that these paths may have dead-ended.
- Electropalatography: capacitative sensing within the mouth
	- a dental retainer-like device—somewhat obtrusive: Kimura, N., Gemicioglu, T., Womack, J., Li, R., Zhao, Y., Bedri, A., Su, Z., Olwal, A., Rekimoto, J., & Starner, T. (2022). SilentSpeller: Towards mobile, hands-free, silent speech text entry using electropalatography. CHI Conference on Human Factors in Computing Systems.
		- “Live text entry speeds for seven participants averaged 37 words per minute at 87% accuracy.”
- Surface electromyography, i.e. detection of motor neuron signals involved in articulation
	- These approaches all involve sensing apparatus which extends onto the jaw or face—i.e. obtrusive!
		- The most promising example I’ve seen here is [[AlterEgo]].
- Motion sensors (accelerometer et al, on the jaw):
	- This class has made less progress until recently, but the deep learning revolution may make this modality possible. The state of the art is still using SVMs, etc:
		- Khanna, P., Srivastava, T., Pan, S., Jain, S., & Nguyen, P. (2021). JawSense: Recognizing Unvoiced Sound using a Low-cost Ear-worn System. Proceedings of the 22nd International Workshop on Mobile Computing Systems and Applications, 44–49. [https://doi.org/10.1145/3446382.3448363](https://doi.org/10.1145/3446382.3448363)
		- Claims 92% accuracy rate for 9 most common phonemes

## References

Apart from the specific systems above, this book offers a helpful survey:
[[Freitas, J., Teixeira, A., Dias, M. S., & Silva, S. (2017). An Introduction to Silent Speech Interfaces. Springer International Publishing]]
