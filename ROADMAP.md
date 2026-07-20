# DeoPrediction Roadmap

## Football

Current football backend and frontend prototype are working.

Next football improvements:
- Better frontend layout
- Fixture detail page
- Prediction detail page
- Market detail page
- More filtering
- Mobile-friendly design

Future football markets to add:
- Corners
- Team corners
- Total corners
- First-half corners
- Asian corner handicap
- Cards
- Booking points
- Team cards
- Player cards
- Player shots
- Player shots on target
- Fouls
- Offsides
- More player/team props
- Draw markets
- Corner markets
- Team corners
- Total corners
- Tackles
- Fouls
- Yellow cards
- GG2+
- Anytime goalscorers
- Player props



## Advanced Football Market Expansion

DeoPrediction should support many markets that normal prediction apps ignore.

Goals and scoring:
- Over 0.5, 1.5, 2.5, 3.5, 4.5
- Under 0.5, 1.5, 2.5, 3.5, 4.5
- BTTS / GG
- BTTS plus over 2.5
- BTTS plus over 3.5
- GG2+
- Team to score 1+
- Team to score 2+
- Team to score 3+
- Both teams over 0.5
- First half goals
- Second half goals
- Highest scoring half
- Goal before minute 30
- Goal after minute 75

Result markets:
- Home win
- Draw
- Away win
- Double chance
- Draw no bet
- Asian handicap
- European handicap
- Win and over goals
- Win and BTTS
- Win to nil
- Comeback possibilities
- Team not to lose

Corners:
- Total corners
- Team corners
- First-half corners
- Second-half corners
- Asian corner handicap
- Race to corners
- Most corners
- Corners plus result builders

Cards and discipline:
- Total yellow cards
- Team yellow cards
- Player cards
- Red card possibility
- Booking points
- First-half cards
- Cards plus result builders

Fouls and tackles:
- Total fouls
- Team fouls
- Player fouls
- Player tackles
- Team tackles
- Fouls drawn
- Referee strictness adjustment

Shots and attacking props:
- Team shots
- Team shots on target
- Player shots
- Player shots on target
- Anytime goalscorer
- First goalscorer
- Player assist possibility
- Goal involvement

Special team trends:
- Team to score in 3 straight matches
- Team to concede in 3 straight matches
- Team clean sheet streak
- Team failed-to-score streak
- Home/away scoring streaks
- Late goal tendency
- Early goal tendency

Bet builder combinations:
- Result plus goals
- Result plus BTTS
- Double chance plus goals
- Team goals plus total goals
- Corners plus cards
- Player shot plus team result
- Goalscorer plus team goals
- Safer low-odds support legs
- Higher-value filtered builders

Data rule:
- Markets are added only when data is good enough.
- Weak markets can still be shown, but must be clearly labelled as higher risk.

## Basketball

Build after football prototype is stable.

Needed:
- Basketball competitions
- Basketball teams
- Basketball fixtures
- Basketball stats
- Basketball predictions
- Basketball markets
- Basketball frontend pages

## Tennis

Build after basketball.

Needed:
- Tennis tournaments
- Tennis players
- Tennis matches
- Tennis rankings
- Tennis form
- Tennis head-to-head
- Tennis predictions
- Tennis markets
- Tennis frontend pages

## Table Tennis

Build after football, basketball, and tennis.

Needed:
- Table tennis competitions
- Table tennis players
- Table tennis matches
- Table tennis form
- Table tennis head-to-head
- Table tennis predictions
- Table tennis markets
- Table tennis frontend pages

## Bet Builders

Build after core markets are reliable.

Football bet builder:
- Match result plus goals
- BTTS plus goals
- Team goals plus result
- Handicap plus goals
- Corners
- Team corners
- Cards
- Player props

Basketball bet builder:
- Moneyline/spread plus totals
- Team totals
- Quarter/half markets
- Player props if data supports it

Tennis bet builder:
- Match winner plus set markets
- Total games
- Handicap games
- Correct set score

Table tennis bet builder:
- Match winner plus game score
- Total points
- Handicap points
- Correct game score

## Zero-Money Deployment Plan

Early testing can run on free tiers for very small usage.

Plan:
- Frontend on free static hosting
- Backend API on free web hosting
- Database on free Postgres
- Telegram bot via cloud webhook
- Laptop should not need to stay on

Known limits:
- Free backend can sleep when inactive
- First request after sleep may be slow
- Free database/storage limits must be watched
- Paid hosting may be needed later for serious 24/7 reliability

## Telegram bot

Build after football, basketball, and tennis core systems are ready.

## Production website

Build final production website after backend sports are stable.
