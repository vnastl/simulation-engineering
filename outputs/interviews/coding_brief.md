# Interview coding brief — target = the 5723 survey schema

Code each VERBATIM-supported construct into the value-labels below. Emit ONLY a listed code. Null over guess. `unaddressed` variables (engineering-insight course, age, ethnicity, religion) are omitted: the interview guide never probes them.


## E. About the respondent
- **gender** (metadata) — gender
    Q: Are you male or female?
    values: 1=male; 2=female
- **school** (strong) — type of secondary school attended
    Q: What type of secondary school did you attend?
    values: 1=Mixed sex; 2=Single sex
- **year** (weak) — year of study
    Q: What year of study are you in?
    values: 1=Part A/Year 1; 2=Part B/Year 2; 3=Part C/Year 3; 4=Part D/Year 4; 5=Placement year
- **dept** (weak) — department
    Q: Which department are you in?
    values: 1=Aeronautical & Automotive Engineering; 2=Chemical Engineering; 3=Civil & Building Engineering; 4=Electronic & Electrical Engineering; 5=IPTME; 6=Mechanical & Manufacturing Engineering; 7=Design & Technology; 8=School of Technology; 9=School of Electronics
- **uni** (weak) — university type (pre- or post-1992)
    Q: Which university are you at?
    values: 1=Pre-1992 university; 2=Post-1992 university

## A. Choosing engineering
- **highsal** (strong) — high salary as a draw to engineering [Influences on the decision to study engineering]
    Q: I was attracted to engineering/design & technology because of the high salary
    values: 1=strongly disagree; 2=disagree; 3=neither agree nor disagree; 4=agree; 5=Strongly agree
- **interest** (strong) — the chance to do interesting work [Influences on the decision to study engineering]
    Q: Engineering/Design & Technology provided an opportunity to do interesting work
    values: 1=strongly disagree; 2=disagree; 3=neither agree nor disagree; 4=agree; 5=Strongly agree
- **challeng** (strong) — wanting the challenge of solving problems [Influences on the decision to study engineering]
    Q: I wanted the challenge of solving problems
    values: 1=strongly disagree; 2=disagree; 3=neither agree nor disagree; 4=agree; 5=Strongly agree
- **special** (strong) — using science and maths without specialising [Influences on the decision to study engineering]
    Q: I wanted to use my science and maths background without specialising in either
    values: 1=strongly disagree; 2=disagree; 3=neither agree nor disagree; 4=agree; 5=Strongly agree
- **mathsci** (strong) — being good at maths and science at school [Influences on the decision to study engineering]
    Q: I was good at maths and science at school
    values: 1=strongly disagree; 2=disagree; 3=neither agree nor disagree; 4=agree; 5=Strongly agree
- **knowledg** (strong) — choosing engineering with little knowledge of the job [Influences on the decision to study engineering]
    Q: I chose to study engineering/design & technology with little knowledge of what engineers actually do
    values: 1=strongly disagree; 2=disagree; 3=neither agree nor disagree; 4=agree; 5=Strongly agree
- **family** (strong) — having a family member in the industry [Influences on the decision to study engineering]
    Q: I knew about engineering/design & technology because a member of my family is involved in the industry
    values: 1=strongly disagree; 2=disagree; 3=neither agree nor disagree; 4=agree; 5=Strongly agree
- **hobbies** (strong) — having technical hobbies and interests [Influences on the decision to study engineering]
    Q: My hobbies and interests are of a technical nature
    values: 1=strongly disagree; 2=disagree; 3=neither agree nor disagree; 4=agree; 5=Strongly agree
- **gooddeg** (strong) — engineering as a good degree to hold regardless [Influences on the decision to study engineering]
    Q: Engineering/Design & Technology will be a good degree to have even if I decide not to enter the profession
    values: 1=strongly disagree; 2=disagree; 3=neither agree nor disagree; 4=agree; 5=Strongly agree
- **varied** (strong) — engineering's appeal as a varied field [Influences on the decision to study engineering]
    Q: Engineering/Design & Technology appealed to me because it is so varied
    values: 1=strongly disagree; 2=disagree; 3=neither agree nor disagree; 4=agree; 5=Strongly agree
- **mother** (strong) — mother's encouragement to study engineering [Influences on the decision to study engineering]
    Q: My mother encouraged me to study engineering/design & technology
    values: 1=strongly disagree; 2=disagree; 3=neither agree nor disagree; 4=agree; 5=Strongly agree
- **father** (strong) — father's encouragement to study engineering [Influences on the decision to study engineering]
    Q: My father encouraged me to study engineering/design & technology
    values: 1=strongly disagree; 2=disagree; 3=neither agree nor disagree; 4=agree; 5=Strongly agree
- **careers** (strong) — careers advisor's encouragement [Influences on the decision to study engineering]
    Q: My careers advisor encouraged me to study engineering/design & technology
    values: 1=strongly disagree; 2=disagree; 3=neither agree nor disagree; 4=agree; 5=Strongly agree
- **teacher** (strong) — school teacher's encouragement [Influences on the decision to study engineering]
    Q: My school teacher encouraged me to study engineering/design & technology
    values: 1=strongly disagree; 2=disagree; 3=neither agree nor disagree; 4=agree; 5=Strongly agree
- **nobody** (strong) — nobody encouraged the choice [Influences on the decision to study engineering]
    Q: Nobody encouraged me to study engineering/design & technology
    values: 1=strongly disagree; 2=disagree; 3=neither agree nor disagree; 4=agree; 5=Strongly agree
- **discoura** (strong) — whether anyone discouraged studying engineering
    Q: Did anyone discourage you from studying engineering/design & technology?
    values: 0=no; 1=yes
- **whodisc** (strong) — who discouraged studying engineering
    Q: If yes, who discouraged you from studying engineering/design & technology?
    values: 1=mother; 2=father; 3=other family; 4=teacher(s); 5=friend(s); 6=engineer(s); 7=careers advisor; 8=other

## B. Experiences of higher education
- **practica** (strong) — the level of practical work being just right [Level of agreement with statements about the degree]
    Q: The level of practical work on the course is just right
    values: 1=strongly disagree; 2=disagree; 3=neither agree nor disagree; 4=agree; 5=Strongly agree
- **curricul** (weak) — the curriculum being harder than expected [Level of agreement with statements about the degree]
    Q: The engineering/design & technology curriculum is more difficult than I expected
    values: 1=strongly disagree; 2=disagree; 3=neither agree nor disagree; 4=agree; 5=Strongly agree
- **pleased** (strong) — being pleased with the choice to study engineering [Level of agreement with statements about the degree]
    Q: I am pleased I chose to study engineering/design & technology
    values: 1=strongly disagree; 2=disagree; 3=neither agree nor disagree; 4=agree; 5=Strongly agree
- **relevanc** (strong) — difficulty seeing the relevance of some modules [Level of agreement with statements about the degree]
    Q: It is difficult to understand the relevance of some modules
    values: 1=strongly disagree; 2=disagree; 3=neither agree nor disagree; 4=agree; 5=Strongly agree
- **competit** (strong) — engineering students being competitive [Level of agreement with statements about the degree]
    Q: Engineering/design & technology students are competitive
    values: 1=strongly disagree; 2=disagree; 3=neither agree nor disagree; 4=agree; 5=Strongly agree
- **Mconfid** (strong) — male students being more confident in class [Level of agreement with statements about the degree]
    Q: Male students are more confident than female students in class
    values: 1=strongly disagree; 2=disagree; 3=neither agree nor disagree; 4=agree; 5=Strongly agree
- **Fhelp** (strong) — female students getting more help in class [Level of agreement with statements about the degree]
    Q: Female students get more help in class than male students
    values: 1=strongly disagree; 2=disagree; 3=neither agree nor disagree; 4=agree; 5=Strongly agree
- **deadline** (weak) — always having competing deadlines [Level of agreement with statements about the degree]
    Q: We always have competing deadlines
    values: 1=strongly disagree; 2=disagree; 3=neither agree nor disagree; 4=agree; 5=Strongly agree
- **assess** (weak) — the coursework/exam balance being just right [Level of agreement with statements about the degree]
    Q: The balance between coursework and exams in module assessments is just right
    values: 1=strongly disagree; 2=disagree; 3=neither agree nor disagree; 4=agree; 5=Strongly agree
- **interper** (strong) — the course developing interpersonal skills [Level of agreement with statements about the degree]
    Q: The course develops interpersonal skills
    values: 1=strongly disagree; 2=disagree; 3=neither agree nor disagree; 4=agree; 5=Strongly agree
- **quality** (strong) — quality of lectures [Satisfaction with aspects of the course]
    Q: Level of satisfaction with quality of lectures
    values: 1=very dissatisfied; 2=dissatisfied; 3=neither satisfied nor dissatisfied; 4=satisfied; 5=very satisfied
- **supplect** (strong) — support from lecturers [Satisfaction with aspects of the course]
    Q: Level of satisfaction with support from lecturers
    values: 1=very dissatisfied; 2=dissatisfied; 3=neither satisfied nor dissatisfied; 4=satisfied; 5=very satisfied
- **supppers** (strong) — support from a personal tutor [Satisfaction with aspects of the course]
    Q: Level of satisfaction with support from personal tutor
    values: 1=very dissatisfied; 2=dissatisfied; 3=neither satisfied nor dissatisfied; 4=satisfied; 5=very satisfied
- **groupwk** (strong) — group work [Satisfaction with aspects of the course]
    Q: Level of satisfaction with group work
    values: 1=very dissatisfied; 2=dissatisfied; 3=neither satisfied nor dissatisfied; 4=satisfied; 5=very satisfied
- **teachhrs** (weak) — number of teaching hours [Satisfaction with aspects of the course]
    Q: Level of satisfaction with number of teaching hours
    values: 1=very dissatisfied; 2=dissatisfied; 3=neither satisfied nor dissatisfied; 4=satisfied; 5=very satisfied
- **friends** (strong) — the friends made on the course [Satisfaction with aspects of the course]
    Q: Level of satisfaction with the friends I've made
    values: 1=very dissatisfied; 2=dissatisfied; 3=neither satisfied nor dissatisfied; 4=satisfied; 5=very satisfied
- **coursewk** (weak) — quantity of coursework [Satisfaction with aspects of the course]
    Q: Level of satisfaction with quantity of coursework
    values: 1=very dissatisfied; 2=dissatisfied; 3=neither satisfied nor dissatisfied; 4=satisfied; 5=very satisfied
- **theory** (weak) — theory work [Satisfaction with aspects of the course]
    Q: Level of satisfaction with theory work
    values: 1=very dissatisfied; 2=dissatisfied; 3=neither satisfied nor dissatisfied; 4=satisfied; 5=very satisfied
- **practwk** (strong) — practical work [Satisfaction with aspects of the course]
    Q: Level of satisfaction with practical work
    values: 1=very dissatisfied; 2=dissatisfied; 3=neither satisfied nor dissatisfied; 4=satisfied; 5=very satisfied
- **designwk** (strong) — design work [Satisfaction with aspects of the course]
    Q: Level of satisfaction with design work
    values: 1=very dissatisfied; 2=dissatisfied; 3=neither satisfied nor dissatisfied; 4=satisfied; 5=very satisfied
- **variety** (strong) — variety of subjects covered [Satisfaction with aspects of the course]
    Q: Level of satisfaction with the variety of subjects the course covers
    values: 1=very dissatisfied; 2=dissatisfied; 3=neither satisfied nor dissatisfied; 4=satisfied; 5=very satisfied

## C. Industrial placement
- **placemen** (strong) — whether they have gone / intend to go on placement
    Q: Have you/do you intend to go on placement?
    values: 0=no; 1=yes
- **experien** (strong) — for the work experience [Reasons for wanting to go on placement]
    Q: I want(ed) to go on placement for the work experience
    values: 1=strongly disagree; 2=disagree; 3=neither agree nor disagree; 4=agree; 5=Strongly agree
- **money** (strong) — because of needing the money [Reasons for wanting to go on placement]
    Q: I want(ed) to go on placement because I need the money
    values: 1=strongly disagree; 2=disagree; 3=neither agree nor disagree; 4=agree; 5=Strongly agree
- **educatio** (strong) — for a break from education [Reasons for wanting to go on placement]
    Q: I want(ed) to go on placement because I need a break from education
    values: 1=strongly disagree; 2=disagree; 3=neither agree nor disagree; 4=agree; 5=Strongly agree
- **jobprosp** (strong) — to improve job chances after university [Reasons for wanting to go on placement]
    Q: I want(ed) to go on placement to improve my chances of getting a job when I finish university
    values: 1=strongly disagree; 2=disagree; 3=neither agree nor disagree; 4=agree; 5=Strongly agree
- **jobdecid** (strong) — to help decide a future direction [Reasons for wanting to go on placement]
    Q: I want(ed) to go on placement to help me decide what I want to do when I finish university
    values: 1=strongly disagree; 2=disagree; 3=neither agree nor disagree; 4=agree; 5=Strongly agree
- **industry** (strong) — to see what industry is really like [Reasons for wanting to go on placement]
    Q: I want(ed) to go on placement to give me an idea of what industry is really like
    values: 1=strongly disagree; 2=disagree; 3=neither agree nor disagree; 4=agree; 5=Strongly agree
- **perdevel** (strong) — for personal development [Reasons for wanting to go on placement]
    Q: I want(ed) to go on placement for personal development
    values: 1=strongly disagree; 2=disagree; 3=neither agree nor disagree; 4=agree; 5=Strongly agree
- **unigrade** (strong) — to improve grades on returning to university [Reasons for wanting to go on placement]
    Q: I want(ed) to go on placement to improve my grades when I return to university
    values: 1=strongly disagree; 2=disagree; 3=neither agree nor disagree; 4=agree; 5=Strongly agree
- **apptheor** (strong) — to apply theory learnt at university [Reasons for wanting to go on placement]
    Q: I want(ed) to go on placement because it will be an opportunity to apply the theory I've learnt at university
    values: 1=strongly disagree; 2=disagree; 3=neither agree nor disagree; 4=agree; 5=Strongly agree
- **finalyr** (strong) — to help choose a final-year project [Reasons for wanting to go on placement]
    Q: I want(ed) to go on placement because it will help me decide what to do for my final year project
    values: 1=strongly disagree; 2=disagree; 3=neither agree nor disagree; 4=agree; 5=Strongly agree
- **indchart** (strong) — because it counts towards Chartership [Reasons for wanting to go on placement]
    Q: I want(ed) to go on placement because the year in industry counts towards getting my Chartership
    values: 1=strongly disagree; 2=disagree; 3=neither agree nor disagree; 4=agree; 5=Strongly agree
- **placothe** (strong) — additional reason for wanting placement
    Q: Additional reasons for wanting to go on placement
    values: 1=compulsory; 2=other
- **wkexp** (strong) — already having work experience [Reasons for not going on placement]
    Q: I do/did not want to on placement because I already have work experience
    values: 1=strongly disagree; 2=disagree; 3=neither agree nor disagree; 4=agree; 5=Strongly agree
- **placloca** (strong) — no placement available in a suitable location [Reasons for not going on placement]
    Q: I do/did not want to on placement because I could not find a placement in a suitable location
    values: 1=strongly disagree; 2=disagree; 3=neither agree nor disagree; 4=agree; 5=Strongly agree
- **breaked** (strong) — fear of returning to education after a break [Reasons for not going on placement]
    Q: I do/did not want to on placement because I thought it would be too difficult to get back into education after a break
    values: 1=strongly disagree; 2=disagree; 3=neither agree nor disagree; 4=agree; 5=Strongly agree
- **finuni** (strong) — wanting to finish university sooner and start earning [Reasons for not going on placement]
    Q: I do/did not want to on placement because I want to finish uni as soon as possible so I can start earning money
    values: 1=strongly disagree; 2=disagree; 3=neither agree nor disagree; 4=agree; 5=Strongly agree
- **nogain** (strong) — seeing nothing to be gained from a placement [Reasons for not going on placement]
    Q: I do/did not want to on placement because I don't think there is anything to be gained from going on placement
    values: 1=strongly disagree; 2=disagree; 3=neither agree nor disagree; 4=agree; 5=Strongly agree
- **noappeal** (strong) — no available placement appealing [Reasons for not going on placement]
    Q: I do/did not want to on placement because I could not find a placement where the work I would be doing appealed to me
    values: 1=strongly disagree; 2=disagree; 3=neither agree nor disagree; 4=agree; 5=Strongly agree
- **noaccept** (strong) — having applied but not been accepted [Reasons for not going on placement]
    Q: I do/did not want to on placement because I applied for placements but was not accepted
    values: 1=strongly disagree; 2=disagree; 3=neither agree nor disagree; 4=agree; 5=Strongly agree
- **noplaoth** (strong) — additional reason for not going on placement
    Q: Additional reasons for not wanting to go on placement
    values: 1=already employed; 2=network 75 student; 3=Armed Forces; 4=time; 5=already completed placement/year out; 6=not required on course; 7=university not supportive; 8=other

## D. Future in engineering
- **carpath** (strong) — preferred area of engineering to specialise in
    Q: What area of engineering/design & technology would you prefer to specialise in?
    values: 1=consultancy; 2=design work; 3=contracting; 4=manufacturing; 5=project management; 6=research/development; 7=teaching; 8=Armed Forces related; 9=don't know; 10=do not want career in engineering; 11=other
- **furstudy** (weak) — whether they would like to go on to further study
    Q: Would you like to go on to further study?
    values: 0=no; 1=yes
- **studarea** (weak) — intended area of further study
    Q: If yes, what area/subject would you like to study?
    values: 1=don't know; 2=PhD; 3=Masters, MSc, MBA; 4=PGCE, teaching; 5=engineering related subject; 6=design related subject; 7=not engineering/design related; 8=other
- **salary** (weak) — salary [Importance of factors when choosing a job]
    Q: Salary will be important to me in making a decision to accept a job or decide where to work
    values: 1=very unimportant; 2=unimportant; 3=neither important nor unimportant; 4=important; 5=very important
- **location** (weak) — location [Importance of factors when choosing a job]
    Q: Location will be important to me in making a decision to accept a job or decide where to work
    values: 1=very unimportant; 2=unimportant; 3=neither important nor unimportant; 4=important; 5=very important
- **workenv** (weak) — work environment [Importance of factors when choosing a job]
    Q: Work environment will be important to me in making a decision to accept a job or decide where to work
    values: 1=very unimportant; 2=unimportant; 3=neither important nor unimportant; 4=important; 5=very important
- **people** (weak) — the people worked with [Importance of factors when choosing a job]
    Q: People I work with will be important to me in making a decision to accept a job or decide where to work
    values: 1=very unimportant; 2=unimportant; 3=neither important nor unimportant; 4=important; 5=very important
- **travel** (weak) — opportunities to travel [Importance of factors when choosing a job]
    Q: Opportunities to travel will be important to me in making a decision to accept a job or decide where to work
    values: 1=very unimportant; 2=unimportant; 3=neither important nor unimportant; 4=important; 5=very important
- **benefits** (weak) — benefits such as a company car [Importance of factors when choosing a job]
    Q: Benefits like a company car will be important to me in making a decision to accept a job or decide where to work
    values: 1=very unimportant; 2=unimportant; 3=neither important nor unimportant; 4=important; 5=very important
- **training** (weak) — training opportunities [Importance of factors when choosing a job]
    Q: Training opportunities will be important to me in making a decision to accept a job or decide where to work
    values: 1=very unimportant; 2=unimportant; 3=neither important nor unimportant; 4=important; 5=very important
- **promot** (weak) — opportunities for promotion [Importance of factors when choosing a job]
    Q: Opportunities for promotion will be important to me in making a decision to accept a job or decide where to work
    values: 1=very unimportant; 2=unimportant; 3=neither important nor unimportant; 4=important; 5=very important
- **equalopp** (weak) — equal-opportunities policies [Importance of factors when choosing a job]
    Q: Equal opportunites policies will be important to me in making a decision to accept a job or decide where to work
    values: 1=very unimportant; 2=unimportant; 3=neither important nor unimportant; 4=important; 5=very important
- **flexible** (weak) — opportunities for flexible working [Importance of factors when choosing a job]
    Q: Opportunities for flexible working will be important to me in making a decision to accept a job or decide where to work
    values: 1=very unimportant; 2=unimportant; 3=neither important nor unimportant; 4=important; 5=very important
- **childcar** (weak) — childcare policies [Importance of factors when choosing a job]
    Q: Child-care policies will be important to me in making a decision to accept a job or decide where to work
    values: 1=very unimportant; 2=unimportant; 3=neither important nor unimportant; 4=important; 5=very important
- **workrole** (strong) — preferred future work role
    Q: In the future what would you prefer your work role to be?
    values: 1=managerial; 2=technical/specialist; 3=don't know
- **charship** (weak) — importance of gaining Chartership
    Q: In your opinion, how important is it for you to get Chartership?
    values: 1=important; 2=not important; 3=not applicable to my subject area