+++
title = "Summary: Post-Quantum Key Exchange (New Hope)"
description = ""
tags = ["Cybersecurity"]
date = "2024-06-26"
categories = ["Summary", "Cybersecurity"]
+++


Andreis Gustavo Malta Purim¹

¹ Institute of Computing, State University of Campinas in Campinas, São Paulo, Brazil. a213095@dac.unicamp.br

**Disclaimer:** This summary is my report for grad-level course MO421 (Cryptographic Algorithms) at UNICAMP. The objective is to explain the New Hope Post-Quantum from a begginers perspective, without sacrificing the technical content. This report was submitted on 30/06/2024 but it may be edited to add more content or clarify some parts in the future.

Also, be aware that this is the first time I add MathJax on my website. Since it's a recent addition, it might not be as stable as I'd like.

# 1. Summary

This summary examines the New Hope proposal for Transport Layer Security (TLS), proposed by Erdem Alkim, Leo Ducas, Thomas Poppelmann, and Peter Schwabe at the USENIX Security Symposium 2016. New Hope was one of the Key Exchange Methods (KEM) proposals submitted to the NIST Post-Quantum Padronization competition. By implementing the Key Exchange, it would ensure that the TLS protocol was safe against quantum computers capable of breaking traditional assymetric encryption.

New Hope was based on the Ring Learning with Errors (Ring-LWE, or simply RLWE) primitive, which itself bases its security on the Lattice-based Short Vector Problem (SVP). By focusing on key optimization and security designs (reconciliation techniques, against all authority design, and others), it provided an optimized but secure way of users conecting to severs throught the internet without being at risk of quantum computers.

The sections of this report will be as follows:

**Sections:**

2. [Introduction to Post-Quantum Lattice-Based Cryptography](#2-introduction-to-post-quantum-lattice-based-cryptography)
3. [The Basics of Ring Learning-With-Errors](#3-the-basics-of-ring-learning-with-errors)
4. [New Hope TLS Proposal](#4-new-hope-tls-proposal)
5. [Comparison with previous works and conclusions](#5-comparison-with-previous-works-and-conclusions)
6. [Sources and Additional Material](#6-sources-and-additional-material)

# 2. Introduction to Post-Quantum Lattice-Based Cryptography

In this section, I'll briefly explain how assymetric cryptography worked and how (and why) quantum computers may break them. I'll also present a new type of mathematical problem that may be used as a basis for a quantum-safe cryptography.

## 2.1 From RSA to Lattices

One of the fundamental pillars of the internet is the capability for two parties to exchange messages privately and securely, even if they have had no prior contact. To achieve this without any intermediaries (such as governments, internet service providers, or any devices intercepting network packets) knowing the contents of the message, these parties must establish a cryptographic key securely. This process must ensure that neither party's private key is ever disclosed or transmitted over the network. This is accomplished using asymmetric cryptography.

For brevity, I'll assume the reader has a basic understanding of classic asymmetric cryptography. In sum, asymmetric cryptography, such as RSA and ElGamal, relies on two parties having private keys (never shared over the air) and public keys (accessible to anyone). When one party wants to contact another, it uses its own private key and the other's public key to generate a shared secret, which only both parties know.

A prime example is the Diffie-Hellman key exchange. Let's consider two users, Alice (A) and Bob (B). Alice and Bob agree on a large prime number $$p$$ and a base $$g$$, which are public. Alice selects a private key $$a$$ and computes her public key $$A=g^a\ mod\ p$$. Similarly, Bob selects a private key $$b$$ and computes his public key $$B=g^b\ mod\ p$$. They exchange their public keys over an insecure channel.

Alice then uses Bob's public key $$B$$ and her private key $$a$$ to compute the shared secret $$K=B^a\ mod\ p$$. Bob uses Alice's public key $$A$$ and his private key $$b$$ to compute the same shared secret $$K=A^b{ }mod{ }p$$. Since $$A=g^a\ mod\ p$$ and $$B=g^b\ mod\ p$$, both calculations result in the same shared secret $$K=g^{ab}\ mod\ p$$. This shared secret can then be used to encrypt further communications between Alice and Bob, ensuring that their messages remain private and secure.

The Diffie-Hellman key exchange is secure under the assumption that the Discrete Logarithm Problem (DLP) is hard for classical computers. That is, it takes a normal computer an extraordinaire (non-polynomial) ammount of time to find the solution to the discrete logarithm. The discrete logarithm problem is defined as follows:

> Given a prime number $$p$$, a base $$g$$ (a primitive root modulo $$p$$), and a value $$h$$, find the exponent $$x$$ such that $$g^x ≡ h\ mod\ p$$.

However, in 1994, Peter Shor published what is now known as Shor's algorithm, a groundbreaking quantum algorithm capable of efficiently factoring the prime factors of integers [1], which can be extended to finding solving the DLP. While the algorithm itself was slow on classical computers, by leveraging quantum quantum Fourier transforms, a quantum computer is capable of finding the solution in $$(\log N)^{2}(\log \log N)(\log \log \log N)$$ time. That is, a polynomial (and rather "fast") time.

While I do not have the time to fully explain Shor's algorithm, this video by _minutephyisics_

{{< youtube lvTqbM5Dq4Q >}}

With Shor's algorithm, it is conceivable that in the coming years, as quantum computers become more stable and capable of handling more qubits, attackers could exploit them to compromise internet security. In fact, it is likely that malicious actors today are already storing encrypted data with the intention of decrypting it in the future when quantum computing resources become available.

With the entirety of classical asymmetric cryptography in jeopardy, a new field has emerged: post-quantum cryptography. This field focuses on developing cryptographic algorithms that are resistant to both classical and quantum computers. Instead of relying on the hardness of problems like the discrete logarithm problem (DLP), which quantum computers can solve efficiently, post-quantum cryptography uses problems that, to our current knowledge, remain computationally difficult for both classical and quantum systems.

One of these very hard mathematical problems is called the _Shortest Vector Problem_ (SVP) in Lattice structures. In mathematics, a lattice refers to a regular arrangement of points in a multi-dimensional space, extending infinitely in all directions. Think of it as a grid that can be formed by combining integer multiples of a set of basis vectors. These basis vectors define the fundamental building blocks of the lattice.

For example, in two-dimensional space (2D), a lattice can be visualized as a grid formed by extending infinitely in both horizontal and vertical directions, with each point on the grid being an integer combination of two chosen vectors, like that seen in Figure 1.

![](/imgs/pqc_new_hope/figure1.png)
**Figure 1.** Lattice $$ℤ^2$$ with basis (0,1) and (1,0) by [2]. 

Note that the same Lattice can be represented by a different basis of vectors, such as seen in Figure 2. Therefore, it is possible to create an "easy" lattice by picking a basis, then creating a second "messy" basis that makes the Lattice harder to solve. This intuitive approach will be important to understand how the SVP problem works.

![](/imgs/pqc_new_hope/figure2.png)
**Figure 1.** The same Lattice $$ℤ^2$$ with basis (1,2) and (2,3) by [2]. 

The Shortest Vector Problem (SVP) is a fundamental challenge within lattice-based cryptography. It involves finding the shortest non-zero vector within a given lattice. Formally, given a lattice defined by its basis vectors, the goal is to identify a lattice point that has the smallest Euclidean norm (length) among all non-zero lattice points.

For instance, imagine you have a lattice defined by two basis vectors in 2D. The SVP asks to find the lattice point that is closest to the origin (0, 0) in terms of Euclidean distance.

The difficulty of the SVP lies in its computational complexity, especially as the dimensionality of the lattice increases and the basis vectors become larger. Finding the shortest vector in high-dimensional lattices can be extremely challenging and is believed to be computationally hard for both classical and quantum computers. This hardness is the basis of many of the post-quantum cryptographic algorithms proposed today, including the New Hope.

The next concept one needs to understand is Learning With Errors, and more specifically, Ring Learning with Errors.

# 3. The Basics of Ring Learning-With-Errors

So far, I've shown how assymetric cryptography worked, why quantum computers may break today's security, and the new mathematical problem that could be used as a basis for our new quantum-safe cryptography. However, this explanation has been - so far - very theoretical. In this section.

## 3.1 The Learning with Errors (LWE) Problem


The Learning with Errors (LWE) problem is a cornerstone of modern lattice-based cryptography and is recognized for its robustness against both classical and quantum attacks. Introduced by Oded Regev in 2005, the LWE problem involves solving systems of linear equations that are perturbed by small random errors. Specifically, the problem can be described as follows: given a set of linear equations with added noise, the goal is to recover the original linear relationships or the secret vectors used to generate them. Mathematically, this can be expressed as finding a vector s\mathbf{s}s given pairs (A,b=As+e)(\mathbf{A}, \mathbf{b} = \mathbf{A}\mathbf{s} + \mathbf{e})(A,b=As+e), where A\mathbf{A}A is a matrix, s\mathbf{s}s is the secret vector, and e\mathbf{e}e is the error vector.

The difficulty of the LWE problem lies in the noise e\mathbf{e}e, which makes it computationally hard to determine the exact vector s\mathbf{s}s. This inherent hardness, which remains even in the presence of quantum computers, forms the basis of the security for LWE-based cryptographic schemes. LWE can be used to construct various cryptographic primitives, including public-key encryption schemes, digital signatures, and homomorphic encryption systems. Its versatility and strong security guarantees make it a fundamental building block in the development of post-quantum cryptography.

## 3.4 The Ring Learning with Errors (Ring-LWE) Problem

The Ring Learning with Errors (Ring-LWE) problem is an extension of the LWE problem, adapted to the structure of polynomial rings. Introduced to improve the efficiency and performance of cryptographic protocols, Ring-LWE leverages the algebraic properties of rings, specifically the ring of polynomials with coefficients modulo a prime number. The main idea is similar to LWE but operates within the context of ring operations, making it more suitable for practical implementations in cryptography.

\begin{aligned}
KL(\hat{y} || y) &= \sum_{c=1}^{M}\hat{y}_c \log{\frac{\hat{y}_c}{y_c}} \\
JS(\hat{y} || y) &= \frac{1}{2}(KL(y||\frac{y+\hat{y}}{2}) + KL(\hat{y}||\frac{y+\hat{y}}{2}))
\end{aligned}

In Ring-LWE, the problem can be described as follows: given a polynomial ring \(R=Z[x]/(f(x))\mathbb{R}\) = \mathbb{Z}[x]/(f(x))R=Z[x]/(f(x)) where \(f(x)f(x)f(x)\) is a polynomial, and given noisy ring equations of the form (a,b=a⋅s+e)(a, b = a \cdot s + e)(a,b=a⋅s+e), the objective is to find the secret polynomial sss. Here, aaa is a known ring element, sss is the secret ring element, and eee is the error polynomial. The structure of the ring allows for more efficient computations and storage, which translates to faster and more compact cryptographic schemes compared to standard LWE.

Ring-LWE maintains the strong security properties of LWE while offering significant performance advantages. This makes it particularly attractive for constructing efficient cryptographic protocols, such as key exchange algorithms and encryption schemes. The New Hope algorithm, which is based on Ring-LWE, is one notable example that has been proposed for securing internet communications against quantum threats. The adaptation of the LWE problem to the ring setting has thus played a crucial role in advancing the practical deployment of quantum-resistant cryptography.

## 3.5 Bit Reconciliation Algorithms

Bit reconciliation algorithms play a critical role in lattice-based key exchange protocols, particularly in ensuring that two parties can securely and efficiently agree on a shared secret key over an insecure channel. These algorithms are essential for correcting errors that arise during the key exchange process, especially when dealing with noisy data as is common in lattice-based schemes.

One of the key contributions to this area was made by Chris Peikert, who introduced efficient bit reconciliation methods to enhance the practicality and security of lattice-based key exchange protocols. The primary challenge these algorithms address is that when two parties exchange information over a noisy channel, the received data may contain discrepancies due to the inherent noise. The goal of bit reconciliation is to align these slightly differing bits so that both parties end up with an identical shared secret.

Peikert's bit reconciliation techniques involve methods for error correction and noise tolerance, allowing the two parties to agree on a common key despite the presence of small errors. These methods typically include:
Error-Correcting Codes: Peikert's approach often leverages error-correcting codes, such as BCH codes or Reed-Solomon codes, which can detect and correct errors in the exchanged data. These codes add redundancy to the transmitted data, enabling the receiver to identify and fix discrepancies introduced by noise.

Cross-Round Error Correction: Another technique involves the use of multiple rounds of communication, where each round helps to refine and correct the bits agreed upon in previous rounds. By iteratively exchanging information and applying error correction, the parties can progressively reduce the error rate and converge on an identical shared secret.
Information Reconciliation Protocols: These protocols ensure that even if the initial data exchanged by the two parties contains errors, they can still align their shared secret through a series of carefully designed communication steps. The protocols typically involve sending auxiliary information that helps in pinpointing and correcting the differing bits without revealing the entire secret.

Peikert's contributions in bit reconciliation have been instrumental in the development of practical lattice-based key exchange protocols. These algorithms ensure that the key exchange process remains secure and efficient, even in the presence of noise, making them suitable for real-world applications such as secure internet communications and post-quantum cryptographic systems.

# 4. New Hope TLS Proposal

## 4.1 Overview of TLS and How It Works

Transport Layer Security (TLS) is a widely used cryptographic protocol designed to provide secure communication over a computer network. TLS ensures privacy, data integrity, and authentication between communicating applications. It is the successor to the Secure Sockets Layer (SSL) protocol and is commonly used to secure web traffic, email, instant messaging, and other forms of data transmission.

TLS works through a series of steps known as the TLS handshake, which establishes a secure session between a client (such as a web browser) and a server (such as a web server). The handshake involves the following key processes:

1. **Negotiation of Security Parameters:** The client and server agree on the version of TLS to use, select cryptographic algorithms (cipher suites), and establish session parameters.
2. **Server Authentication and Pre-Master Secret Exchange:** The server provides a digital certificate to authenticate its identity. The client then generates a pre-master secret and securely transmits it to the server, typically encrypted using the server's public key.
3. **Session Key Generation:** Both parties use the pre-master secret along with other data exchanged during the handshake to generate a symmetric session key, which will be used to encrypt and decrypt data during the session.
4. **Secure Data Transmission:** Once the handshake is complete and a secure session is established, the client and server can exchange data encrypted with the session key, ensuring confidentiality and integrity.

## 4.2. The Bos et al. (BCNS) Proposal for TLS

In response to the impending threat posed by quantum computers, researchers including Bos, Costello, Naehrig, and Stebila (BCNS) proposed a quantum-resistant key exchange mechanism for TLS, known as the New Hope algorithm. This proposal builds upon the lattice-based cryptographic techniques, particularly those leveraging the Ring Learning with Errors (Ring-LWE) problem, and incorporates the efficient bit reconciliation methods introduced by Chris Peikert.
The BCNS proposal, often referred to as New Hope, integrates these advanced cryptographic ideas into the TLS protocol to provide quantum-resistant security. The main features and steps of the New Hope key exchange process in TLS are as follows:

Ring-LWE Based Key Exchange: The New Hope algorithm uses the Ring-LWE problem to generate cryptographic keys that are secure against quantum attacks. The client and server exchange Ring-LWE samples to establish a shared secret.
Bit Reconciliation: To ensure that both parties derive the same shared secret despite the noise in the exchanged data, the New Hope algorithm employs bit reconciliation techniques. These methods, inspired by Peikert's work, involve error-correcting codes and cross-round error correction protocols to align the slightly differing bits, ensuring that both parties end up with an identical secret key.

Integration into TLS Handshake: The New Hope key exchange mechanism is seamlessly integrated into the standard TLS handshake process. After negotiating security parameters and authenticating the server, the client and server use the New Hope algorithm to securely exchange key material and generate a symmetric session key. This session key is then used for encrypting the subsequent data transmission, just as in traditional TLS.

The importance of the BCNS proposal lies in its ability to provide a practical and efficient post-quantum security solution for TLS, ensuring that secure communications can withstand the advances in quantum computing. By implementing the New Hope algorithm within the TLS protocol, the BCNS proposal offers a robust framework for quantum-resistant key exchange, addressing the need for forward-secure cryptographic systems that can protect sensitive data in the quantum era. This advancement represents a significant step forward in the development of practical post-quantum cryptographic solutions, ensuring the continued security of internet communications.

# 5. Comparison with previous works and conclusions

# 6. Sources and Additional Material

[1] P. W. Shor, "Algorithms for quantum computation: discrete logarithms and factoring," Proceedings 35th Annual Symposium on Foundations of Computer Science, Santa Fe, NM, USA, 1994, pp. 124-134, doi: 10.1109/SFCS.1994.365700.

[2] Hesamian, Seyedamirhossein, "Analysis of BCNS and Newhope Key-exchange Protocols" (2017). Theses and Dissertations. 1485. https://dc.uwm.edu/etd/1485

http://web.eecs.umich.edu/~cpeikert/pubs/suite.pdf
https://summerschool-croatia.cs.ru.nl/2018/slides/Introduction%20to%20post-quantum%20cryptography%20and%20learning%20with%20errors.pdf
https://math.colorado.edu/~kstange/teaching-resources/crypto/RingLWE-notes.pdf
https://asecuritysite.com/pqc/lwe_output
https://eprint.iacr.org/2010/613.pdf
https://eprint.iacr.org/2012/230.pdf
https://eprint.iacr.org/2014/599.pdf
https://security.googleblog.com/2016/07/experimenting-with-post-quantum.html
https://asecuritysite.com/encryption/lwe3
https://asecuritysite.com/encryption/lwe2
https://asecuritysite.com/encryption/lwe
https://github.com/scottwn/PyNewHope
https://asecuritysite.com/pqc/newhope
https://newhopecrypto.org/
https://www.usenix.org/conference/usenixsecurity16/technical-sessions/presentation/alkim
