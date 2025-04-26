import { useState, useEffect } from "react";

function App() {
	const [data, setData] = useState([]);
	const [input, setInput] = useState("");

	const fetchData = async () => {
		try {
			let res = await fetch("http://127.0.0.1:8000/messages");
			if (!res.ok) {
				throw new Error(`HTTP error! status: ${res.status}`);
			}
			let d = await res.json();
			setData(d);
		} catch (error) {
			console.error("Failed to fetch data:", error);
		}
	};

	useEffect(() => {
		fetchData();
	}, []);

	const submitHandler = async () => {
		try {
			const response = await fetch("http://127.0.0.1:8000/messages", {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
				},
				body: JSON.stringify(input),
			});

			if (!response.ok) {
				throw new Error(`HTTP error! status: ${response.status}`);
			}

			const data = await response.json();
			console.log("Success:", data);
		} catch (error) {
			console.error("Error:", error);
		}
	};

	const changeHandler = (e) => {
		e.preventDefault();
		setInput(e.target.value);
	};

	return (
		<main className="h-[500px] w-full grid grid-cols-12 gap-4">
			<section className="p-5 flex shrink-0 bg-red-100 flex-1 h-full col-span-4 border-gray-300 rounded-md border-2">
				<ul>
					{data &&
						data.map((msg) => {
							if (msg.role === "user") {
								return (
									<li className="p-2 rounded-md m-2 bg-blue-400">
										{msg.content}
									</li>
								);
							}
							if (msg.role === "system") {
								return (
									<li className="p-2 rounded-md m-2 bg-green-400">
										{msg.content}
									</li>
								);
							}
						})}
				</ul>
			</section>
			<section className="p-5 border-gray-300 rounded-md border-2 col-span-8 flex flex-1">
				<ul>
					{data &&
						data.map((msg) => {
							if (msg.data) {
								return (
									<li className="text-sm text-gray-700 my-2 border-gray-300 p-2 border-2">
										{msg.data}
									</li>
								);
							}
						})}
				</ul>
			</section>
			<section>
				<form onSubmit={submitHandler}>
					<input value={input} onChange={(e) => changeHandler(e)} type="text" />
					<button type="submit">Submit</button>
				</form>
			</section>
		</main>
	);
}

export default App;
