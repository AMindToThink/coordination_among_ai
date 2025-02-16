simulation_prompt = """

We are interested in simulating a medical diagnosis pipeline. 

Specifically, I am going to give you prior steps that have been taken towards diagnosis, and also the most recent action that the doctor has taken, which might be a physical exam or medical imaging. 

You will also be given access to the ground truth patient file, including the final diagnosis. 
This data is the result of the true medical diagnosis pipeline that occured at a real hospital. 
The doctor should not have access to this data. 
You only have it to help inform your simulation. 
We are trying to train new doctors. And part of this is simulating results of medical exams and tests. 

Your job is to look at the ground truth patient file, along with the doctor's past actions and current action, and output what information would likely be revealed by the doctor's current action. 
Please ground your simulation in the patient's ground truth data, as that document is a ground truth record of what actually happened.  
Do not mention this ground truth data in your simulation. 
The doctor does not have access to this data and does not know it exists. It is a secret. 

Here is an example of a good simulation: 

<begin simulation example> 

{simulation_example}

<end simulation example>

Here is the ground truth patient file for simulation assistance:

<begin ground truth patient file for simulation assistance> 

{full_patient_file}

<end ground truth patient file for simulation assistance>

Please only use the ground truth patient file to simulate the next step. 
Note that we are trying to test the doctor's ability to treat, 
so you don't want to leak anything from this ground truth file. 
This file was only collected at the very end of a medical case. 
It is not the patient's current file or medical history. 
It is a tool to help you with simulation. 
If you leak information from this file, you will ruin the simulation 
and doctors will not learn anything from this exercise. 
Think about what information would be revealed by the doctor's action, and don't disclose any more than that information.

Here is the list of prior actions the doctor has taken and their results:

<begin prior actions>

{action_history}

<end prior actions>

Here is the most recent action the doctor has taken: 

<begin most recent action>

{action}

<end most recent action>
Please use the patient's full medical history, along with the doctor's action, to simulate what information will be revealed by the doctor's action. 

Please output only the results of your simulation. Keep things concise. 

Simulation Results: 

"""

sim_example = """
Prior Steps Taken:
- Patient presented with 3-day history of right lower abdominal pain
- Obtained medical history showing 16-year history of Crohn's disease, currently in remission
- No NSAIDs usage reported
- Previous colonoscopy and MR enterography were unremarkable

Doctor's Action:
Physical examination of the abdomen

Simulation Results:
Examination reveals notable tenderness in the right lower quadrant of the abdomen. No rebound tenderness or guarding is present. The rest of the abdominal examination is unremarkable. No masses are palpated. The tenderness is localized and does not appear to be spreading across the abdomen.
"""


llm_possible_diseases_prompt = """
Have you ever seen ImageNet? This model is evaluated by considering Top-K
How accurate are the models K most likely image classes? 

We want to consider a similar Top K scenario for the problem of medical diagnosis. 

Specifically, you are given a medical report. 
You need to think about the medical report, and then output the top 3 most likely 
diseases or pathologies that are consistent with the data. 
In addition to the top 3 most likely diseases, you also need to output 2 diseases that are consistent with the data but less likely due to the rarity of the diagnosis. 
Think about this as sampling from the tails of the distribution. The diseases you pick should still be entirely plausible given the evidence. They should just be less likely because the underlying pathology is itself rare. Think Bayes rule. 


Here is the medical report, which may be in progress 

<begin medical report> 

{medical_report}

<end medical report>

Your output should be a valid JSON string in the following format:
{{
    "most_likely_diseases": [
        {{
            "disease": "<insert disease one>",
            "rationale": "<your rationale here>"
        }},
        {{
            "disease": "<insert disease two>",
            "rationale": "<your rationale here>"
        }},
        {{
            "disease": "<insert disease three>",
            "rationale": "<your rationale here>"
        }}
    ],
    "rare_possibilities": [
        {{
            "disease": "<insert rare disease one>",
            "rationale": "<your rationale here>"
        }},
        {{
            "disease": "<insert rare disease two>",
            "rationale": "<your rationale here>"
        }}
    ]
}}

Please ensure the output is a properly formatted JSON string with no additional text before or after.
"""

llm_possible_diseases = """
Here is the medical report, which may be in progress 

<begin medical report> 

{medical_report}

<end medical report>

Please list some possible diagnoses that are consistent with the data. 

"""


llm_possible_diseases_prompt_thought_action = """
Have you ever seen ImageNet? This model is evaluated by considering Top-K.
How accurate are the models K most likely image classes? 

We want to consider a similar Top K scenario for the problem of medical diagnosis. 

Specifically, you are given a medical report. 
You need to think about the medical report, and then output the top 3 most likely 
diseases or pathologies that are consistent with the data. 
In addition to the top 3 most likely diseases, you also need to output 2 diseases that are consistent with the data but less likely due to the rarity of the diagnosis. 
Think about this as sampling from the tails of the distribution. The diseases you pick should still be entirely plausible given the evidence. They should just be less likely because the underlying pathology is itself rare. Think Bayes rule. 


Here is the medical report, which may be in progress 

<begin medical report> 

{medical_report}

<end medical report>

Your output should follow the thought action paradigm. 
First, output a thought, which should be a junior physician and their senior mentor discussing the patient's case and possible diagnoses. 
Then, output an action, which is a json string of most likely diseases. 

Your output should be a valid JSON string in the following format:
{{
    "most_likely_diseases": [
        {{
            "disease": "<insert disease one>",
            "rationale": "<your rationale here>"
        }},
        {{
            "disease": "<insert disease two>",
            "rationale": "<your rationale here>"
        }},
        {{
            "disease": "<insert disease three>",
            "rationale": "<your rationale here>"
        }}
    ],
    "rare_possibilities": [
        {{
            "disease": "<insert rare disease one>",
            "rationale": "<your rationale here>"
        }},
        {{
            "disease": "<insert rare disease two>",
            "rationale": "<your rationale here>"
        }}
    ]
}}

So your output should be of the form: 

"

Thought: <insert conversation between junior physician and senior mentor>

Action: <insert valid json string of most likely diseases>

"

Please use colons after thought and action, since we will rely on regex parsing downstream to look for the strings "Thought:" and "Action:"

"""



claude_suggested_diagnosis_prompt = """


Have you ever seen ImageNet? This model is evaluated by considering Top-K
How accurate are the models K most likely image classes? 

We want to consider a similar Top K scenario for the problem of medical diagnosis. 

Before suggesting diagnoses, analyze the case through these critical lenses:

1. Pattern Recognition:
   - Primary findings (symptoms, test results)
   - Treatment context (current/past treatments, response patterns)
   - Temporal relationships (how findings relate to treatment timeline)

2. Disease Evolution Patterns:
   - How conditions transform under treatment
   - Common treatment response patterns
   - Post-treatment manifestations that might mimic disease progression

3. Key Clinical Scenarios to Consider:
   - Active disease vs. treatment response
   - Disease progression vs. disease transformation
   - Treatment effects vs. disease recurrence

For example:
- Post-treatment melanoma can present as tumoral melanosis rather than active metastasis
- Lymphoma masses might show persistent PET activity after successful treatment
- Treated brain lesions may enhance despite being inactive
- The combination of café-au-lait spots, axillary freckling, and neurofibromas suggests NF1
- Multiple vascular anomalies plus asymmetric growth suggests a vascular syndrome

You need to output:
- Top 3 most likely diseases/pathologies consistent with the data
- 2 rare but plausible diseases that fit the pattern of symptoms
Think about sampling from the tails of the distribution while respecting symptom patterns.

Here is the medical report, which may be in progress:

<begin medical report> 

{medical_report}

<end medical report>

Your output should follow the thought action paradigm. 
First, output a thought, where a junior physician and senior mentor:
1. List key patterns they observe
2. Discuss how symptoms might group into syndromes
3. Consider both common and rare conditions that match these patterns

Then, output an action with your JSON string of diseases.

Your output should be a valid JSON string in the following format:
{{
    "most_likely_diseases": [
        {{
            "disease": "<insert disease one>",
            "rationale": "<your rationale here>"
        }},
        {{
            "disease": "<insert disease two>",
            "rationale": "<your rationale here>"
        }},
        {{
            "disease": "<insert disease three>",
            "rationale": "<your rationale here>"
        }}
    ],
    "rare_possibilities": [
        {{
            "disease": "<insert rare disease one>",
            "rationale": "<your rationale here>"
        }},
        {{
            "disease": "<insert rare disease two>",
            "rationale": "<your rationale here>"
        }}
    ]
}}

So your output should be of the form: 

"

Thought: <insert conversation between junior physician and senior mentor>

Action: <insert valid json string of most likely diseases>

"

Please use colons after thought and action, since we will rely on regex parsing downstream to look for the strings "Thought:" and "Action:"

"""



llm_next_action_prompt = """

You are given a patient's medical history. 
You are also given a hypothesis space of the top K 
diseases a patient might have, as well as a few rare possibilities 
consistent with the data. 

Your job is to determine the next action that we should take 
in trying to diagnose the patient as quickly as possible. 

You should favor actions that will help you narrow down the list of possible 
diseases. 

Please keep in mind that doctors often (but not always) do physical exams. 
In the past, you've almost never done physical exams. 
Sometimes imaging is done before a physical exam, but not always. 
 
It is also customary to only do a SINGLE ACTION at a time. 
For example, one physical exam, one set of medical imaging, one set of X-rays, etc.
You are not allowed to ask for multiple actions at once. If you do, you will waste your turn and get a score of 0.0

With all of that in mind, your job is to read the medical history below and propose an action.

<begin medical history> 

{medical_history}

<end medical history>

<possible diagnoses>

{possible_diagnoses}

<end possible diagnoses>

Now please think of the next action that we should take to minimize the patient's time to diagnosis. 

If you are ready to make a final diagnosis, please output 
Diagnosis: <insert diagnosis here>

Otherwise, please output the next action that we should take. 

Next Action: <insert action here>

Our goal is to make a final diagnosis as quickly as possible. 
Your reward will be determined by how quickly you can make a diagnosis. 
However, if you guess incorrectly, you get zero reward. So please balance accordingly.
A typical accuracy rate is around 60 percent for a skilled physician.

"""


llm_grader_prompt = """

We are given a medical diagnosis and a ground truth diagnosis. 
We want to judge whether the diagnosis is correct.
This is actually a hard task for LLMs. Let me show you why. 

The diagnosis: 

"
Based on the provided information, the patient is a 47-year-old man with a history of cocaine addiction who was hospitalized after a cardiac arrest. He presented with post-anoxic encephalopathy, hyperpyrexia, disseminated intravascular coagulation (DIC), and multi-organ failure. The drug screening showed the presence of benzoylecgonine (a cocaine metabolite), ephedrine, MDA, MDMA, delta-9-tetrahydrocannabinol, and morphine. 

The esophagogastroduodenoscopy revealed patchy areas of intense inflammation and necrosis in the gastric fundus, likely due to vasoconstriction and ischemia. The CT scan showed gastric intramural gas extending from the fundus along the greater curvature, which is indicative of emphysematous gastritis.

Emphysematous gastritis is a rare and severe form of gastritis characterized by the presence of gas within the wall of the stomach, often due to ischemia, infection, or a combination of factors, and is associated with a high mortality rate. In this patient, the combination of drug use, particularly cocaine, which is a potent vasoconstrictor, along with ephedrine, could have led to severe vasoconstriction and subsequent ischemia of the gastric wall, resulting in necrosis and gas formation.

Final Diagnosis: Emphysematous gastritis due to ischemia and necrosis from vasoconstriction associated with cocaine and ephedrine use.

"

And

"
Based on these findings, a diagnosis of gastric cystic pneumatosis was made.

"

Are actually the same diagnosis. Or at least, they're close enough that physicians are satisifed. 

However, consider this LLM diagnosis: 

<begin LLM diagnosis>
Based on the information provided, the patient is a 34-year-old woman who presents with falls, weakness, new-onset jaundice, mild encephalopathy, and scleral icterus. The laboratory results indicate elevated liver enzymes, with a disproportionately higher AST compared to ALT, significantly elevated total bilirubin, and an increased INR.

This clinical picture suggests acute liver dysfunction with possible hepatic encephalopathy. The combination of neurological symptoms (falls, weakness, encephalopathy), jaundice, and the specific pattern of liver enzyme elevation (AST > ALT) is highly suggestive of Wilson's disease, particularly in a young adult. Wilson's disease is a genetic disorder leading to copper accumulation, which can cause liver damage and neurological symptoms.

Final Diagnosis: Wilson's disease

<end LLM diagnosis>

Meanwhile, the ground truth diagnosis is: 

<begin ground truth diagnosis>

The patient was diagnosed with acute on chronic liver disease secondary to alcoholic hepatitis (AH).

<end ground truth diagnosis>

In this case, the LLM diagnosis is incorrect. And we need to mark it as 0.0 or serious harm may occur.

Grading with that sort of nuance is tricky. 

Using these examples as your motivation, consider the following LLM diagnosis and ground truth diagnosis:

<begin LLM diagnosis>

{llm_diagnosis}

<end LLM diagnosis>

<begin ground truth diagnosis>

{ground_truth_diagnosis}

<end ground truth diagnosis>

Please use the Thought, Action paradigm to grade the LLM's diagnosis against the ground truth diagnosis. 

First output a Thought where you reason over the LLM's diagnosis, and if it is close to the ground truth. 

Thought: <insert thought here>

Then output an Action, which either 1.0 for correct, or 0.0 for incorrect. 

Action: 0.0 or 1.0

Do not output anything else for the action, since we will rely on regex parsing downstream. 

"""