import React from 'react';
import ReactDOM from 'react-dom/client';
import {
  createBrowserRouter,
  RouterProvider,
  Route,
  Link,
} from "react-router-dom";
import Markdown from 'react-markdown'



function importAll(r) {
  return r.keys().map(r);
}

const rawArticles =  importAll(require.context('./files', false, /\.md/)).map(file => 
  fetch(file).then((response) => response.text()).then((text) => {
    return {name: file, text: text}
  }
))


function App(){
  const [articles, setArticles] = React.useState()
  React.useEffect(()=>{
    async function fetchData() {
      Promise.all(rawArticles).then((values) => {
        setArticles(values)
      });
    }
    fetchData()
  }, [])



  if(articles){
      return(
      
      // <Routes>


      //</Routes>
      <>
      {articles?articles.map(art=> <div><Markdown>{art.text}</Markdown></div>):null}
      </>
    )}
  else{
    return(<h1>Loading</h1>)
  }
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
