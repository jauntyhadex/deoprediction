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
