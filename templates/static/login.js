const submit = document.getElementByid("submit");

submit.addEvenlistener('click', () =>{
    fetch("/login",{
        method:"POST",
        body: new formdata(form)
    })
   .then(res => res.json())
   .then(data =>) {
       alert(data.message);
       window.location.herf ="home.html";
  }  
});
