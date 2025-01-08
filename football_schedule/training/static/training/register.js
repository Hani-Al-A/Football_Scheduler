document.addEventListener('DOMContentLoaded', function() {

    document.querySelector('#user_time_zone').value = Intl.DateTimeFormat().resolvedOptions().timeZone

    if (document.querySelector("#team_of_user").value !== ""){
        document.querySelector("#afterTeamSelect").style.display = "block";
    } else{
        document.querySelector("#afterTeamSelect").style.display = "none";
    }
    
    document.querySelectorAll('.must_select').forEach((e) => {
        e.addEventListener('change', () =>{
            const user_is_coach = document.querySelector('#job_title').value;
            const team_selected = document.querySelector('#team').value;
            const player = document.querySelector('#player');
            const coach = document.querySelector('#coach');



            if (user_is_coach !== 'none' && team_selected !== ""){
                if(user_is_coach === 'True'){
                    coach.style.display = "block";
                    player.value = "none";
                    player.style.display = "none";

                } else{
                    player.style.display = "block";
                    coach.value = "none";
                    coach.style.display = "none";
                }
                document.querySelector('.register_details').style.display = "block";

            }
            else{
                document.querySelector('.register_details').style.display = "none";
            }

        })
    });
    

});

