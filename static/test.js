// let interests = [];
// function addInterest(e) {
//     const interest = document.getElementById("interest").value;
//     interests.push(interest);
//     document.getElementById("interest").value = '';
//     e.preventDefault();
// }
// function register() {
//     const email = document.getElementById('email').value;
//     const pass = document.getElementById("pass").value;
//     $.ajax({
//         url: '/register',
//         type: 'POST',
//         contentType: 'application/json',
//         data: JSON.stringify({ 'interests': interests, 'email': email, "pass": pass }),
//         success: function (response) {
//             // console.log(response)
//             document.getElementById('email').value = '';
//             document.getElementById("pass").value = '';
//         },
//         error: function (error) {
//             console.log(error);
//         }
//     });
// }