// ============================================================
// BEEHIIV INJECTION SCRIPT — The Fight Docket
// Run this in the browser console on the Beehiiv editor page
// ============================================================

(async function injectAndClean() {
  const editor = document.querySelector('.ProseMirror');
  if (!editor) { console.error('ProseMirror editor not found'); return; }

  // Step 1: Focus and select all existing content
  editor.focus();
  document.execCommand('selectAll', false, null);

  // Step 2: Inject clean HTML
  const CLEAN_HTML = `<div style="max-width:680px; margin:0 auto; background-color:#0D0D0D; font-family:Georgia,'Times New Roman',serif; color:#F2F2E8;">
<!-- HEADER -->
  <div style="background:#0D0D0D; border-top:6px solid #DE1E20; padding:36px 40px 28px 40px;">
    <p style="margin:0 0 1px 0; font-family:Arial,Helvetica,sans-serif; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:8px; color:#C5A059;">The</p>
    <div style="font-family:Arial Black,Impact,Helvetica,sans-serif; font-size:56px; font-weight:900; text-transform:uppercase; color:#F2F2E8; line-height:0.95; letter-spacing:-2px; margin:0 0 16px 0;">FIGHT<br>DOCKET</div>
    <div style="height:1px; background:#C5A059; margin:0 0 12px 0;"></div>
    <p style="margin:0 0 4px 0; font-family:Arial,Helvetica,sans-serif; font-size:10px; text-transform:uppercase; letter-spacing:4px; color:#C5A059;">Boxing &middot; MMA &middot; The Stories Behind The Sport</p>
    <p style="margin:0; font-family:Arial,Helvetica,sans-serif; font-size:11px; text-transform:uppercase; letter-spacing:2px; color:#555;">AUGUST 10, 2026</p>
  </div>
<!-- CONTENT -->
  <div style="padding:0 40px 48px 40px;">
<!-- EDITOR'S NOTE -->
    <div style="padding-top:40px;">
      <p style="margin:0 0 5px 0; font-family:Arial,Helvetica,sans-serif; font-size:9px; font-weight:700; text-transform:uppercase; letter-spacing:4px; color:#C5A059;">Editor's Note</p>
      <div style="width:40px; height:3px; background:#DE1E20; margin-bottom:22px;"></div>
      <img src="https://i.ibb.co/F4pM2My4/nb2-2026-08-10-intro.jpg" alt="intro" style="width:100%; max-width:600px; display:block; margin:0 0 28px 0; border:1px solid #1E1E1E;">
<div style="color:#F2F2E8;"><p style='color:#F2F2E8;'>The theme of the past week was market disruption. In the ring, a wave of new world champions were crowned in boxing, while a stunning upset in the UFC scrambled the lightweight title picture. Outside the cage, a major merger consolidated the industry's second-tier promotional landscape, creating a more formidable challenger to the UFC's market dominance. Every pillar of the combat sports ecosystem, from talent to titles to television rights, saw a significant variable change.</p><p style='color:#F2F2E8;'>My read is that we are witnessing the direct consequences of long-term strategic plays. The PFL's merger with Most Valuable Promotions is the culmination of years of capital raises and roster-building aimed at creating a viable alternative for top-tier talent. Meanwhile, the UFC's continued global expansion, evidenced by a slew of new international media deals, is running in parallel with its high-stakes domestic rights negotiations with ESPN. The outcomes in the ring are providing the fuel for these business maneuvers.</p><p style='color:#F2F2E8;'>This issue dissects the operational impact of the new titleholders in boxing, the financial underpinnings of the PFL/MVP merger, and the career-altering economics of Quillan Salkilld's shocking victory. The pieces on the board have been reshuffled, and the next moves by promoters and networks will define the competitive landscape for the remainder of the year.</p></div>
    </div>
<div style="height:1px; background:#1E1E1E; border-top:1px solid #C5A059; opacity:0.25; margin:40px 0;"></div>
<!-- MAIN STORY -->
    <div>
      <p style="margin:0 0 5px 0; font-family:Arial,Helvetica,sans-serif; font-size:9px; font-weight:700; text-transform:uppercase; letter-spacing:4px; color:#DE1E20;">Main Story</p>
      <div style="width:40px; height:3px; background:#DE1E20; margin-bottom:22px;"></div>
      <img src="https://i.ibb.co/842WrrB5/nb2-2026-08-10-main-story.jpg" alt="main_story" style="width:100%; max-width:600px; display:block; margin:0 0 28px 0; border:1px solid #1E1E1E;">
<h2 style="font-family:Arial Black,Impact,Helvetica,sans-serif; font-size:28px; font-weight:900; line-height:1.2; margin:0 0 22px 0; letter-spacing:-0.5px; color:#F2F2E8; text-transform:uppercase;">NEW KINGS CROWNED: BOXING SEES THREE MAJOR TITLE SHIFTS IN 48 HOURS</h2>
      <div style="color:#F2F2E8;"><p style='color:#F2F2E8;'>The championship landscape in professional boxing was significantly reordered this past weekend, with three separate weight classes seeing new world titleholders emerge. The results from Saturday and Sunday create fresh matchups for unification, establish new divisional power brokers, and reset the commercial trajectory for the victors.</p><p style='color:#F2F2E8;'>On Saturday, August 8, Ireland's Aaron McKenna captured the vacant IBF middleweight title with a unanimous decision victory over Etinosa Oliha. The win positions McKenna as a key player at 160 pounds, a division ripe for high-stakes unification bouts against other belt-holders. His ascension provides a new European focal point in a historically competitive weight class.</p><p style='color:#F2F2E8;'>The title turnover continued on Sunday, August 9. Tamm Thibeault claimed both the IBF and WBO middleweight titles by defeating Desley Robinson, consolidating a significant portion of the divisional hardware. In the bantamweight division, Dina Thorslund defeated Cherneka Johnson by unanimous decision to become the undisputed champion, a status that brings maximum leverage in future negotiations. These victories are not just athletic achievements; they are asset acquisitions that grant the fighters and their promoters control over a piece of the market.</p><p style='color:#F2F2E8;'>In MMA, the weekend's biggest result was not a title change but had a similar disruptive effect. At UFC Fight Night on Saturday, unranked Quillan Salkilld submitted the highly-touted Mateusz Gamrot in the first round. This result instantly inserts Salkilld into the lightweight top ten and derails Gamrot's path to a title shot. The financial delta is massive: Salkilld moves from a standard fight purse to a position where he can command main-event money and contender-level contract terms.</p><p style='color:#F2F2E8;'>What this signals to the market is a fundamental reshuffling across multiple combat sports. New champions mean new mandatory challengers must be negotiated with, new unification pathways open up, and broadcast partners have fresh storylines to promote. The balance of power has shifted, and the financial and strategic fallout will unfold over the coming months.</p></div>
    </div>
<div style="height:1px; background:#C5A059; opacity:0.2; margin:40px 0;"></div>
<!-- LEGAL TRACKER -->
    <div>
      <p style="margin:0 0 5px 0; font-family:Arial,Helvetica,sans-serif; font-size:9px; font-weight:700; text-transform:uppercase; letter-spacing:4px; color:#DE1E20;">Legal Tracker</p>
      <div style="width:40px; height:3px; background:#DE1E20; margin-bottom:22px;"></div>
      <img src="https://i.ibb.co/F4NpYjRq/nb2-2026-08-10-legal.jpg" alt="legal" style="width:100%; max-width:600px; display:block; margin:0 0 28px 0; border:1px solid #1E1E1E;">
<p style="font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:2px; color:#DE1E20; margin:0 0 20px 0;">Active Federal Cases</p>
      <p style='margin:0 0 20px 0; color:#F2F2E8;'><strong style='color:#F2F2E8;'>Johnson et al. v. Zuffa, LLC (D. Nev. 2:21-cv-01189)</strong><br><span style='color:#888;'>Last activity: Feb. 25, 2026</span>. The filing reveals plaintiffs moved for severe sanctions, up to and including default judgment, against Zuffa. The motion is based on allegations of spoliation, or the intentional destruction of evidence relevant to the antitrust claims. This is the most critical pending motion in the case, as a finding of spoliation could be catastrophic for the defense.<br><em style='color:#888;'>Status: Motion for sanctions pending.</em></p><p style='margin:0 0 20px 0; color:#F2F2E8;'><strong style='color:#F2F2E8;'>Costantino et al. v. Zuffa, LLC (2:26-cv-00539)</strong><br><span style='color:#888;'>Last activity: Feb. 26, 2026</span>. A new complaint was filed, representing another class of fighters and continuing the legal pressure on UFC's parent company, TKO Group Holdings, over its labor and compensation practices.<br><em style='color:#888;'>Status: Complaint filed; defendant response pending.</em></p><p style='margin:0 0 20px 0; color:#F2F2E8;'>No new disciplinary actions, suspensions, or adverse drug test findings were reported by the NYSAC, CSAC, or NSAC in the past week's available records.</p>
    </div>
<div style="height:1px; background:#C5A059; opacity:0.2; margin:40px 0;"></div>
<!-- RUMOR MILL -->
    <div>
      <p style="margin:0 0 5px 0; font-family:Arial,Helvetica,sans-serif; font-size:9px; font-weight:700; text-transform:uppercase; letter-spacing:4px; color:#DE1E20;">Rumor Mill</p>
      <div style="width:40px; height:3px; background:#DE1E20; margin-bottom:22px;"></div>
      <img src="https://i.ibb.co/RkMDtF0J/nb2-2026-08-10-rumor.jpg" alt="rumor" style="width:100%; max-width:600px; display:block; margin:0 0 28px 0; border:1px solid #1E1E1E;">
<div style='border-left:3px solid #C5A059; padding:4px 0 4px 18px; margin-bottom:28px;'>
        <p style='font-family:Arial,Helvetica,sans-serif; font-size:9px; font-weight:700; text-transform:uppercase; letter-spacing:3px; color:#C5A059; margin:0 0 10px 0;'>CONFIDENCE 0.90</p>
        <p style='margin:0; color:#F2F2E8; line-height:1.8;'>Following his dominant victory on August 1, boxer Raymond Muratalla is planning a division change. Sources close to the fighter's camp indicate a move up in weight is imminent to pursue more significant title opportunities. (Source: Boxing media reports)</p>
      </div><div style='border-left:3px solid #888888; padding:4px 0 4px 18px; margin-bottom:28px;'>
        <p style='font-family:Arial,Helvetica,sans-serif; font-size:9px; font-weight:700; text-transform:uppercase; letter-spacing:3px; color:#888888; margin:0 0 10px 0;'>CONFIDENCE 0.65</p>
        <p style='margin:0; color:#F2F2E8; line-height:1.8;'>The management for UFC Featherweight Champion Ilia Topuria is signaling a hardline stance against cross-promotional talks, with his manager publicly stating Topuria would "annihilate 100%" of a rival promotion's roster. This is likely posturing to strengthen their negotiating position within the UFC. (Source: MMAFighting)</p>
      </div><div style='border-left:3px solid #444444; padding:4px 0 4px 18px; margin-bottom:28px;'>
        <p style='font-family:Arial,Helvetica,sans-serif; font-size:9px; font-weight:700; text-transform:uppercase; letter-spacing:3px; color:#444444; margin:0 0 10px 0;'>CONFIDENCE 0.40</p>
        <p style='margin:0; color:#F2F2E8; line-height:1.8;'>As part of the recent merger with Most Valuable Promotions, the Professional Fighters League (PFL) brand will be fully phased out by early 2027. While the merger itself is confirmed, the specific timeline for rebranding remains fluid and subject to integration challenges. (Source: MMA Junkie)</p>
      </div>
    </div>
<div style="height:1px; background:#C5A059; opacity:0.2; margin:40px 0;"></div>
<!-- FIGHT CARD PREVIEWS -->
    <div>
      <p style="margin:0 0 5px 0; font-family:Arial,Helvetica,sans-serif; font-size:9px; font-weight:700; text-transform:uppercase; letter-spacing:4px; color:#DE1E20;">Fight Card Previews</p>
      <div style="width:40px; height:3px; background:#DE1E20; margin-bottom:22px;"></div>
      <img src="https://i.ibb.co/gMXcwCB7/nb2-2026-08-10-fight-previews.jpg" alt="fight_previews" style="width:100%; max-width:600px; display:block; margin:0 0 28px 0; border:1px solid #1E1E1E;">
<h2 style="font-family:Arial Black,Impact,Helvetica,sans-serif; font-size:22px; font-weight:900; line-height:1.2; margin:0 0 20px 0; letter-spacing:-0.5px; color:#F2F2E8; text-transform:uppercase;">UFC 330 Headlines a Loaded Stretch</h2>
      <div style="color:#F2F2E8;"><p style='color:#F2F2E8;'><strong style='color:#F2F2E8;'>UFC 330: Makhachev vs. Machado Garry</strong><br><span style='color:#888;'>Saturday, August 15 &middot; Xfinity Mobile Arena, Philadelphia</span></p>
      <p style='color:#F2F2E8;'>The card the entire second half of the year runs through. Islam Makhachev defending against Ian Machado Garry is the rare pay-per-view that carries genuine business weight, landing inside TKO's exclusive negotiating window with ESPN. A dominant title defense strengthens the promotion's leverage at exactly the moment it needs a marquee number to point at. An upset creates a new franchise name with a fresh contract cycle ahead of him. Either way, the buy rate becomes a data point in a nine-figure negotiation.</p>
      <p style='color:#F2F2E8;'>Note the timing. Quillan Salkilld's win over Mateusz Gamrot reshuffled the lightweight contender pool eight days before the belt is contested. Whoever walks out of Philadelphia with the title inherits a division whose queue was rewritten last weekend.</p>
      <p style='color:#F2F2E8;'><strong style='color:#F2F2E8;'>Also on the calendar:</strong></p>
      <ul style='color:#F2F2E8; padding-left:20px; margin:0 0 18px 0;'>
        <li style='margin-bottom:8px; line-height:1.7; color:#F2F2E8;'><strong style='color:#F2F2E8;'>Aug. 22</strong> &middot; UFC Fight Night: Hernandez vs. Rodrigues, Golden 1 Center, Sacramento</li>
        <li style='margin-bottom:8px; line-height:1.7; color:#F2F2E8;'><strong style='color:#F2F2E8;'>Aug. 29</strong> &middot; UFC Fight Night: Nurmagomedov vs. Song, Oriental Sports Center, Shanghai</li>
        <li style='margin-bottom:8px; line-height:1.7; color:#F2F2E8;'><strong style='color:#F2F2E8;'>Sept. 5</strong> &middot; UFC Fight Night: Hooker vs. Parnasse, Accor Arena, Paris</li>
      </ul>
      <p style='color:#F2F2E8;'>The Shanghai and Paris dates are worth watching as business events rather than sporting ones. Both slot into the international rights strategy laid out in this issue's Business Intel, feeding the same market expansion that produced the Paramount+ Canada and DAZN Germany deals.</p>
      <p style='color:#F2F2E8;'>No major boxing cards had been finalized as of press time. Check thefightdocket.com Friday evening for the updated slate.</p></div>
    </div>
<div style="height:1px; background:#C5A059; opacity:0.2; margin:40px 0;"></div>
<!-- BUSINESS INTEL -->
    <div>
      <p style="margin:0 0 5px 0; font-family:Arial,Helvetica,sans-serif; font-size:9px; font-weight:700; text-transform:uppercase; letter-spacing:4px; color:#DE1E20;">Business Intel</p>
      <div style="width:40px; height:3px; background:#DE1E20; margin-bottom:22px;"></div>
      <img src="https://i.ibb.co/fz6ZpsZH/nb2-2026-08-10-business-intel.jpg" alt="business_intel" style="width:100%; max-width:600px; display:block; margin:0 0 28px 0; border:1px solid #1E1E1E;">
<h2 style="font-family:Arial Black,Impact,Helvetica,sans-serif; font-size:22px; font-weight:900; line-height:1.2; margin:0 0 20px 0; letter-spacing:-0.5px; color:#F2F2E8; text-transform:uppercase;">PFL MERGES WITH MVP AS TKO ENTERS EXCLUSIVE ESPN WINDOW</h2>
      <div style="color:#F2F2E8;"><p style='color:#F2F2E8;'>The combat sports promotional landscape has consolidated further with the confirmation that the Professional Fighters League (PFL) will merge with Jake Paul's Most Valuable Promotions (MVP). The move creates a unified entity aimed at competing more directly with market leader TKO Group Holdings. Reporting indicates the PFL brand will be phased out as operations are integrated under the MVP banner, a strategic decision to leverage MVP's significant media footprint.</p><p style='color:#F2F2E8;'>This merger occurs at a critical juncture for TKO, which has entered a three-month exclusive negotiating window with ESPN for its domestic UFC media rights. This negotiation is the single most significant financial event on TKO's horizon, with the current deal's value serving as the baseline for a potentially massive increase. The outcome will dictate a substantial portion of UFC's revenue for the next broadcast cycle.</p><p style='color:#F2F2E8;'>TKO's focus on media rights is global. Last week, the company announced an expansion with Paramount+ to make the streaming service the exclusive home for UFC numbered events in Canada for six years, beginning in 2027. This follows a three-year extension with DAZN for rights in Germany and Austria and a new deal with Arena Sport in the Balkans. The strategy is clear: lock down key international markets to diversify revenue streams ahead of the domestic rights renewal.</p><p style='color:#F2F2E8;'>These strategic maneuvers are backed by strong financials. TKO reported Q2 2026 revenue of $1.547 billion with $303.9 million in net income. The company also disclosed an approximate $30 million loss on its recent UFC Freedom 250 event at the White House, signaling a willingness to absorb significant costs for events deemed to have high brand value, even without direct profitability.</p></div>
    </div>
<div style="height:1px; background:#C5A059; opacity:0.2; margin:40px 0;"></div>
<!-- FIGHTER SPOTLIGHT -->
    <div>
      <p style="margin:0 0 5px 0; font-family:Arial,Helvetica,sans-serif; font-size:9px; font-weight:700; text-transform:uppercase; letter-spacing:4px; color:#DE1E20;">Fighter Spotlight</p>
      <div style="width:40px; height:3px; background:#DE1E20; margin-bottom:22px;"></div>
      <img src="https://i.ibb.co/7thpQG1b/nb2-2026-08-10-fighter-spotlight.jpg" alt="fighter_spotlight" style="width:100%; max-width:600px; display:block; margin:0 0 28px 0; border:1px solid #1E1E1E;">
<h2 style="font-family:Arial Black,Impact,Helvetica,sans-serif; font-size:22px; font-weight:900; line-height:1.2; margin:0 0 20px 0; letter-spacing:-0.5px; color:#F2F2E8; text-transform:uppercase;">QUILLAN SALKILLD</h2>
      <div style="color:#F2F2E8;"><p style='color:#F2F2E8;'>Quillan Salkilld's first-round submission of Mateusz Gamrot at UFC Vegas 120 was not just an upset; it was a fundamental alteration of his career's economic and competitive trajectory. In four minutes and twenty-five seconds, Salkilld transformed from a promising but unranked lightweight into a legitimate top-10 contender in the UFC's most competitive division. Gamrot, a fighter widely considered to be on the cusp of a title shot, saw his momentum erased, illustrating the brutal volatility of the sport.</p><p style='color:#F2F2E8;'>The financial implications of this single victory are profound. Salkilld's market value has increased by an order of magnitude. His next contract negotiation will start from a position of immense leverage, allowing his management to command figures typical of a main-event talent. Performance bonuses, sponsorship opportunities, and a higher base pay are now on the table. He has effectively leapfrogged years of divisional climbing, bypassing the arduous and less lucrative path of grinding out wins on the undercard.</p><p style='color:#F2F2E8;'>From a competitive standpoint, the UFC matchmaking office now has a new, marketable Australian contender to inject into the title picture. A logical next step would be a bout against a fighter ranked between 5 and 10, a gatekeeper to the division's absolute elite. A matchup against a name like Beneil Dariush or a fellow rising contender would serve as a barometer for Salkilld's true ceiling. Commercially, this fight is an easy sell: the underdog who pulled off one of the year's biggest upsets now faces his next test. For Salkilld, the pressure is now to prove that Saturday night was not an anomaly, but the new standard.</p></div>
    </div>
</div>
<!-- FOOTER -->
  <div style="border-top:1px solid #C5A059; background:#0D0D0D; padding:32px 40px 36px 40px;">
    <p style="margin:0 0 2px 0; font-family:Arial,Helvetica,sans-serif; font-size:9px; font-weight:700; text-transform:uppercase; letter-spacing:6px; color:#C5A059;">The Fight Docket</p>
    <p style="margin:0 0 16px 0; font-family:Arial,Helvetica,sans-serif; font-size:9px; text-transform:uppercase; letter-spacing:3px; color:#888888;">Boxing &middot; MMA &middot; The Stories Behind The Sport</p>
    <p style="margin:0 0 6px 0; font-family:Arial,Helvetica,sans-serif; font-size:13px; color:#888888;">
      <a href="https://www.thefightdocket.com/" style="color:#DE1E20; text-decoration:none;">www.thefightdocket.com</a>
      &nbsp;&middot;&nbsp;
      Tips &amp; sources: <a href="mailto:tips@thefightdocket.com" style="color:#DE1E20; text-decoration:none;">tips@thefightdocket.com</a>
    </p>
    <p style="margin:12px 0 0 0; font-family:Arial,Helvetica,sans-serif; font-size:11px; color:#777777;">You're receiving this because you subscribed. Forward to a fight fan who thinks like an analyst.</p>
    <p style="margin:6px 0 0 0; font-family:Arial,Helvetica,sans-serif; font-size:11px; color:#777777;">Not subscribed yet? Join free &rarr; <a href="https://www.thefightdocket.com/" style="color:#DE1E20; text-decoration:none;">www.thefightdocket.com</a></p>
  </div>
</div>`;
  document.execCommand('insertHTML', false, CLEAN_HTML);

  // Step 3: Wait one tick for ProseMirror to process
  await new Promise(r => setTimeout(r, 500));

  // Step 4: Post-injection cleanup — remove any stray empty block elements
  const allBlocks = Array.from(editor.querySelectorAll('p, div'));
  let removed = 0;
  allBlocks.forEach(el => {
    if (el.textContent.trim() === '' && !el.querySelector('img')) {
      el.remove();
      removed++;
    }
  });

  // Step 5: Fire input event so Beehiiv autosave picks up the changes
  editor.dispatchEvent(new InputEvent('input', { bubbles: true, cancelable: true }));

  console.log(`✅ Injected successfully. Cleaned up ${removed} empty block elements.`);
})();
